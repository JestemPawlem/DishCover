import json
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
from pgvector.psycopg import register_vector
import psycopg
from tqdm.auto import tqdm

from src.config import (
    DB_URI,
    RECIPES_PARQUET_PATH,
    RECIPE_EMBEDDINGS_PATH
)


BATCH_SIZE = 4096

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
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
    if not os.path.exists(RECIPES_PARQUET_PATH) or not os.path.exists(RECIPE_EMBEDDINGS_PATH):
        logger.error('Required artifact files missing at %s or %s', RECIPES_PARQUET_PATH, RECIPE_EMBEDDINGS_PATH)
        sys.exit(1)

    start_time = time.perf_counter()
    logger.info('Loading preprocessed recipes from %s...', RECIPES_PARQUET_PATH)
    recipes = pd.read_parquet(RECIPES_PARQUET_PATH)

    logger.info('Loading recipe embeddings from %s...', RECIPE_EMBEDDINGS_PATH)
    embeddings = np.load(RECIPE_EMBEDDINGS_PATH)
    logger.info('Artifacts loaded in %.2f s.', time.perf_counter() - start_time)

    n_recipes = len(recipes)
    n_embeddings = len(embeddings)
    if n_recipes != n_embeddings:
        logger.error('Length mismatch: recipes (%d) vs embeddings (%d)', n_recipes, n_embeddings)
        sys.exit(1)

    embedding_dim = embeddings.shape[1]
    logger.info('Found %d recipes with %d-dimensional embeddings.', n_recipes, embedding_dim)

    ids = recipes['id'].to_numpy()
    names = recipes['name'].to_numpy()
    minutes = recipes['minutes'].to_numpy()
    descriptions = recipes['description'].to_numpy()
    raw_ingredients = recipes['ingredients'].to_numpy()
    raw_steps = recipes['steps'].to_numpy()
    raw_ingredient_ids = recipes['ingredient_ids'].to_numpy()
    interaction_counts = recipes['interaction_count'].to_numpy()

    logger.info('Connecting to PostgreSQL at %s...', DB_URI.split('@')[-1])
    try:
        with psycopg.connect(DB_URI, autocommit=True) as conn:
            register_vector(conn)

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'recipes');"
                )
                if not cur.fetchone()[0]:
                    logger.error("Table 'recipes' does not exist. Ensure 01_schema.sql executed on DB initialization.")
                    sys.exit(1)

                logger.info('Temporarily dropping indexes for fast bulk ingestion...')
                cur.execute('DROP INDEX IF EXISTS idx_recipes_name_trgm;')
                cur.execute('DROP INDEX IF EXISTS idx_recipes_like_count;')
                cur.execute('DROP INDEX IF EXISTS idx_recipes_embedding_hnsw;')

                start_time = time.perf_counter()

                logger.info('Ingesting %d records in batches of %d...', n_recipes, BATCH_SIZE)
                with tqdm(total=n_recipes, desc='Seeding Recipes', unit='rec') as pbar:
                    for i in range(0, n_recipes, BATCH_SIZE):
                        end_idx = min(i + BATCH_SIZE, n_recipes)
                        records = [
                            (
                                int(ids[j]),
                                str(names[j]),
                                int(minutes[j]) if pd.notna(minutes[j]) else None,
                                str(descriptions[j]) if pd.notna(descriptions[j]) else None,
                                json.dumps(to_python_list(raw_ingredients[j])),
                                json.dumps(to_python_list(raw_steps[j])),
                                [int(x) for x in to_python_list(raw_ingredient_ids[j])],
                                int(interaction_counts[j]) if pd.notna(interaction_counts[j]) else 0,
                                embeddings[j],
                            )
                            for j in range(i, end_idx)
                        ]
                        cur.executemany(
                            '''
                            INSERT INTO recipes (
                                id, name, minutes, description, ingredients, steps, 
                                ingredient_ids, like_count, embedding
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                            ''', records)
                        pbar.update(len(records))

                total_time = time.perf_counter() - start_time
                logger.info(
                    'Ingestion finished in %.2f s (%.2f rec/s).',
                    total_time,
                    n_recipes / total_time,
                )

                logger.info('Rebuilding performance and vector indexes...')
                indexes = [
                    (
                        'idx_recipes_name_trgm',
                        'CREATE INDEX IF NOT EXISTS idx_recipes_name_trgm ON recipes USING gin (name gin_trgm_ops);',
                    ),
                    (
                        'idx_recipes_like_count',
                        'CREATE INDEX IF NOT EXISTS idx_recipes_like_count ON recipes (like_count DESC);',
                    ),
                    (
                        'idx_recipes_embedding_hnsw',
                        'CREATE INDEX IF NOT EXISTS idx_recipes_embedding_hnsw ON recipes USING hnsw (embedding vector_cosine_ops);',
                    ),
                ]

                for name, ddl in indexes:
                    start_time = time.perf_counter()
                    logger.info('Building %s...', name)
                    cur.execute(ddl)
                    logger.info('Index %s created in %.2f s.', name, time.perf_counter() - start_time)

        logger.info('Database seeding pipeline completed successfully.')

    except psycopg.OperationalError as e:
        logger.error('Connection failed: could not reach PostgreSQL instance (%s).', e)
        sys.exit(1)
    except Exception as e:
        logger.exception('Unexpected error during seeding: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    seed_database()