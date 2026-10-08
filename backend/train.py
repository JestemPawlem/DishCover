import argparse
import datetime
import json
import logging
import os
import sys
import time

from dotenv import load_dotenv
import numpy as np
import pandas as pd
import torch

from ml.evaluation import generate_recipe_embeddings
from ml.training import train


load_dotenv()

DEFAULT_ARTIFACTS_DIR = os.getenv('ARTIFACTS_DIR', 'artifacts')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_training(artifacts_dir: str,
                 epochs: int,
                 batch_size: int,
                 lr: float,
                 embedding_dim: int,
                 temperature: float,
                 eval_k: int) -> None:
    recipes_path = os.path.join(artifacts_dir, 'recipes.parquet')
    interactions_path = os.path.join(artifacts_dir, 'interactions.parquet')

    if not os.path.exists(recipes_path) or not os.path.exists(interactions_path):
        logger.error('Missing required preprocessed datasets.')
        sys.exit(1)

    logger.info('Loading preprocessed datasets...')
    start_time = time.perf_counter()
    recipes = pd.read_parquet(recipes_path)
    interactions = pd.read_parquet(interactions_path)
    logger.info('Loaded %d recipes and %d interactions in %.2fs.',
                len(recipes), len(interactions), time.perf_counter() - start_time)

    logger.info('Starting model training...')
    result = train(
        recipes=recipes,
        interactions=interactions,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        embedding_dim=embedding_dim,
        temperature=temperature,
        eval_k=eval_k
    )
    logger.info('Model training finished in %.2fs.', time.perf_counter() - start_time)

    os.makedirs(artifacts_dir, exist_ok=True)
    weights_path = os.path.join(artifacts_dir, 'two_tower.pt')
    torch.save(result.model.state_dict(), weights_path)
    logger.info('Model weights saved to %s.', weights_path)

    timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')
    metadata_path = os.path.join(artifacts_dir, f'training_metadata_{timestamp}.json')
    metadata_payload = {
        'hyperparameters': result.hyperparameters,
        'best_metrics': result.best_metrics,
        'history': result.history
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_payload, f, indent=2)
    logger.info('Training metadata saved to %s.', metadata_path)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info('Generating offline recipe embeddings on %s...', device)
    start_time = time.perf_counter()
    result.model.eval()

    recipe_embeddings = generate_recipe_embeddings(result.model, recipes, device).cpu().numpy()

    embeddings_path = os.path.join(artifacts_dir, 'recipe_embeddings.npy')
    np.save(embeddings_path, recipe_embeddings)
    logger.info(
        'Saved %d embeddings to %s in %.2fs.',
        recipe_embeddings.shape[0],
        embeddings_path,
        time.perf_counter() - start_time,
    )
    logger.info('Training completed successfully.')


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description='Train Two-Tower recommender and export inference embeddings.',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument(
      '--artifacts-dir',
      type=str,
      default=DEFAULT_ARTIFACTS_DIR,
      help='Directory where input data lives and output artifacts will be saved.',
  )
  parser.add_argument(
      '--epochs', type=int, default=30, help='Total training epochs.'
  )
  parser.add_argument(
      '--batch-size',
      type=int,
      default=2048,
      help='Batch size for training and validation.',
  )
  parser.add_argument(
      '--lr',
      type=float,
      default=1e-2,
      help='Initial learning rate for AdamW.',
  )
  parser.add_argument(
      '--embedding-dim',
      type=int,
      default=128,
      help='Latent embedding vector dimension.',
  )
  parser.add_argument(
      '--temperature',
      type=float,
      default=0.15,
      help='Softmax temperature scaling factor.',
  )
  parser.add_argument(
      '--eval-k',
      type=int,
      default=20,
      help='Cutoff threshold for Recall@k and Jaccard@k.',
  )
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  run_training(
      artifacts_dir=args.artifacts_dir,
      epochs=args.epochs,
      batch_size=args.batch_size,
      lr=args.lr,
      embedding_dim=args.embedding_dim,
      temperature=args.temperature,
      eval_k=args.eval_k,
  )