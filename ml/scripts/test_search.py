import argparse
import logging
import sys
import time

from pgvector.psycopg import register_vector
import psycopg

from src.config import DB_URI


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_similarity_search(target_recipe_id: int,
                          db_uri: str = DB_URI,
                          top_k: int = 5) -> None:
    logger.info('Connecting to PostgreSQL at %s...', db_uri.split('@')[-1])

    try:
        with psycopg.connect(db_uri) as connection:
            register_vector(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT id, name, embedding
                    FROM recipes
                    WHERE id = %s;
                    ''',
                    (target_recipe_id,)
                )
                base_record = cursor.fetchone()

                if not base_record:
                    logger.error('Recipe with ID %d not found in database.', target_recipe_id)
                    sys.exit(1)

                id, name, query_vector = base_record

                logger.info('Found base recipe [%d] \'%s\'', id, name)

                logger.info('Executing HNSW cosine similarity search (Top %d)...', top_k)
                start_time = time.perf_counter()
                cursor.execute(
                    '''
                    SELECT
                        id,
                        name,
                        1 - (embedding <=> %s) AS similarity_score
                    FROM recipes
                    WHERE id != %s
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    ''',
                    (query_vector, target_recipe_id, query_vector, top_k)
                )
                results = cursor.fetchall()
                logger.info('Query completed in %.2f ms. Retrieved %d recommendations.',
                            time.perf_counter() - start_time, len(results))

                header = f"{'Rank':<5} | {'ID':<7} | {'Similarity':<10} | {'Recipe Name':<40}"
                separator = '-' * len(header)
                print(f'\n{separator}\n{header}\n{separator}')

                for rank, (cand_id, cand_name, score) in enumerate(results, start=1):
                    print(f'{rank:<5} | {cand_id:<7} | {score:>9.4f}  | {cand_name:<40}')

                print(f'{separator}\n')

    except psycopg.OperationalError as e:
        logger.error('Database connection erorr: %s', e)
        sys.exit(1)
    except Exception as e:
        logger.exception('An unexpected error occured during search: %s', e)
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Test pgvector HNSW similarity search on seeded recipes.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--recipe-id',
        type=int,
        default=0,
        help='ID of the base recipe to query recommendations for.'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of nearest neighbors to retrieve.'
    )
    parser.add_argument(
        '--db-uri',
        type=str,
        default=DB_URI,
        help='PostgreSQL connection string.'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_similarity_search(
        target_recipe_id=args.recipe_id,
        db_uri=args.db_uri,
        top_k=args.top_k
    )