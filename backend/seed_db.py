import json
import logging
import os
import sys
import time

from dotenv import load_dotenv
import numpy as np
import pandas as pd
from pgvector.psycopg import register_vector
import psycopg
from tqdm.auto import tqdm


load_dotenv()

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'recipes_db')
DB_URI = os.getenv('DATABASE_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
ARTIFACTS_DIR = os.getenv('ARTIFACTS_DIR', 'artifacts')
RECIPES_PATH = os.path.join(ARTIFACTS_DIR, 'recipes.parquet')
EMBEDDINGS_PATH = os.path.join(ARTIFACTS_DIR, 'recipe_embeddings.npy')
BATCH_SIZE = 2048


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def to_python_list(val: object) -> list:
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, (list, tuple)):
        return list(val)
    if val is None:
        return []
    return [val]


def seed_database() -> None:
    if not os.path.exists(RECIPES_PATH) or not os.path.exists(EMBEDDINGS_PATH):
        logger.error('Required artifacts files missing.')
        sys.exit(1)

    start_time = time.perf_counter()

    logger.info('Loading preprocessed recipes from %s...', RECIPES_PATH)
    recipes = pd.read_parquet(RECIPES_PATH)

    logger.info('Loading recipe embeddings from %s...', EMBEDDINGS_PATH)
    embeddings = np.load(EMBEDDINGS_PATH)

    logger.info('Artifacts loaded in %.2f seconds.', time.perf_counter() - start_time)

    n_recipes = len(recipes)
    n_embeddings = len(embeddings)
    if n_recipes != n_embeddings:
        logger.error('Length mismatch: len(recipes) = %d, len(embeddings) = %d', n_recipes, n_embeddings)
        sys.exit(1)

    embedding_dim = embeddings.shape[1]
    logger.info('Found %d recipes with %d-dimensional embeddings.', n_recipes, embedding_dim)


    start_time = time.perf_counter()
    logger.info('Extracting features for fast batching...')
    ids = recipes['id'].to_numpy()
    names = recipes['name'].to_numpy()
    minutes = recipes['minutes'].to_numpy()
    descriptions = recipes['description'].to_numpy()
    raw_ingredients = recipes['ingredients'].to_numpy()
    raw_steps = recipes['steps'].to_numpy()
    raw_ingredient_ids = recipes['ingredient_ids'].to_numpy()
    interaction_counts = recipes['interaction_count'].to_numpy()
    logger.info('Feature extraction finished in %.2f seconds.', time.perf_counter() - start_time)


    logger.info('Connecting to PostgreSQL at %s...', DB_URI.split('@')[-1])
    try:
        with psycopg.connect(DB_URI, autocommit=True) as conn:
            with conn.cursor() as cur:
                logger.info('Enabling pgvector extension if not present...')
                cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            
            register_vector(conn)

            with conn.cursor() as cur:
                logger.info('Ensuring table \'recipes\' exists...')
                cur.execute(f'''
                    CREATE TABLE IF NOT EXISTS recipes(
                        id BIGINT PRIMARY KEY,
                        name TEXT NOT NULL,
                        minutes INT,
                        description TEXT,
                        ingredients JSONB,
                        steps JSONB,
                        ingredient_ids INT[],
                        like_count INT NOT NULL DEFAULT 0,
                        embedding vector({embedding_dim})
                    );
                ''')

                logger.info('Dropping existing indexes during ingestion...')
                cur.execute('DROP INDEX IF EXISTS idx_recipes_like_count;')
                cur.execute('DROP INDEX IF EXISTS recipes_embedding_hnsw_idx;')

                upsert_query = '''
                    INSERT INTO recipes (
                        id, name, minutes, description, ingredients, steps, ingredient_ids,
                        like_count, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        minutes = EXCLUDED.minutes,
                        description = EXCLUDED.description,
                        ingredients = EXCLUDED.ingredients,
                        steps = EXCLUDED.steps,
                        ingredient_ids = EXCLUDED.ingredient_ids,
                        like_count = EXCLUDED.like_count,
                        embedding = EXCLUDED.embedding;
                '''

                start_time = time.perf_counter()
                logger.info('Ingesting %d records in batches of %d...', n_recipes, BATCH_SIZE)

                with tqdm(total=n_recipes, desc='Seeding Recipes', unit='rec') as pbar:
                    for i in range(0, n_recipes, BATCH_SIZE):
                        end_idx = min(i + BATCH_SIZE, n_recipes)

                        records = [
                            (
                                int(ids[j]),
                                names[j],
                                int(minutes[j]),
                                descriptions[j],
                                json.dumps(to_python_list(raw_ingredients[j])),
                                json.dumps(to_python_list(raw_steps[j])),
                                [int(x) for x in to_python_list(raw_ingredient_ids[j])],
                                int(interaction_counts[j]),
                                embeddings[j]
                            )
                            for j in range(i, end_idx)
                        ]

                        cur.executemany(upsert_query, records)
                        pbar.update(len(records))

                total_time = time.perf_counter() - start_time
                logger.info('Database ingestion completed in %.2f seconds (%.2f recipes/sec).', total_time, n_recipes / total_time)

                start_time = time.perf_counter()
                logger.info('Building B-Tree index on like_count...')
                cur.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_recipes_like_count
                    ON recipes (like_count DESC)
                    '''
                )
                logger.info('B-Tree index built in %.2f seconds.', time.perf_counter() - start_time)

                start_time = time.perf_counter()
                logger.info('Building HNSW cosine similarity index...')
                cur.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS recipes_embedding_hnsw_idx
                    ON recipes USING hnsw (embedding vector_cosine_ops);
                    '''
                )
                logger.info('HNSW index built in %.2f seconds.', time.perf_counter() - start_time)

            logger.info('Database seeding completed successfully.')

    except psycopg.OperationalError as e:
        logger.error('Connection failed: could not reach PostgreSQL instance. (%s)', e)
        sys.exit(1)
    except Exception as e:
        logger.exception('An unexpected error occurred during database seeding: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    seed_database()