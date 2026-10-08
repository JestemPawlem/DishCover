import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv
import kagglehub
import pandas as pd

from ml.preprocessing import preprocess


load_dotenv()

DEFAULT_ARTIFACTS_DIR = os.getenv('ARTIFACTS_DIR', 'artifacts')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('preprocess')


def run_preprocessing(
        artifacts_dir: str,
        min_ingredient_count: int,
        min_user_interactions: int,
        min_recipe_interactions: int) -> None:
    logger.info('Starting preprocessing...')
    os.makedirs(artifacts_dir, exist_ok=True)

    logger.info('Downloading dataset...')
    start_time = time.perf_counter()
    dataset_path = kagglehub.dataset_download('shuyangli94/food-com-recipes-and-user-interactions')
    logger.info('Dataset ready at %s (took %.2fs)', dataset_path, time.perf_counter() - start_time)

    recipes_path = os.path.join(dataset_path, 'RAW_recipes.csv')
    interactions_path = os.path.join(dataset_path, 'RAW_interactions.csv')
    if not os.path.exists(recipes_path) or not os.path.exists(interactions_path):
        logger.error('Required CSV files missing.')
        sys.exit(1)

    logger.info('Loading CSV files...')
    start_time = time.perf_counter()
    recipes = pd.read_csv(recipes_path)
    interactions = pd.read_csv(interactions_path)
    logger.info('Loaded %d recipes and %d interactions in %.2fs.',
                len(recipes), len(interactions), time.perf_counter() - start_time)

    logger.info('Preprocessing datasets...')
    start_time = time.perf_counter()
    data = preprocess(
        recipes=recipes,
        interactions=interactions,
        min_ingredient_count=min_ingredient_count,
        min_user_interactions=min_user_interactions,
        min_recipe_interactions=min_recipe_interactions,
        artifacts_dir=artifacts_dir
    )
    logger.info('Preprocessing finished in %.2fs. Retained %d recipes and %d interactions.',
                time.perf_counter() - start_time, len(data.recipes), len(data.interactions))

    logger.info('Saving artifacts...')
    data.save_artifacts(output_dir=artifacts_dir)
    logger.info('Preprocessing completed successfully.')


def parse_args() ->argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run feature preprocessing pipeline for recipes and interactions.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--artifacts-dir',
        type=str,
        default=DEFAULT_ARTIFACTS_DIR,
        help='Directory to save generated artifacts.'
    )
    parser.add_argument(
        '--min-ingredient-count',
        type=int,
        default=10,
        help='Minimum frequency threshold for an ingredient to be retained.'
    )
    parser.add_argument(
        '--min-user-interactions',
        type=int,
        default=2,
        help='Minimum number of ratings required for a user to be included.'
    )
    parser.add_argument(
        '--min-recipe-interactions',
        type=int,
        default=10,
        help='Minimum number of ratings for a recipe to be included.'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_preprocessing(
        artifacts_dir=args.artifacts_dir,
        min_ingredient_count=args.min_ingredient_count,
        min_user_interactions=args.min_user_interactions,
        min_recipe_interactions=args.min_recipe_interactions
    )