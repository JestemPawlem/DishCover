import os
from pathlib import Path
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / '.env')

ARTIFACTS_DIR = Path(os.getenv('ARTIFACTS_DIR', ROOT_DIR / 'artifacts'))
RUNS_DIR = ARTIFACTS_DIR / 'runs'

RECIPES_PARQUET_PATH = ARTIFACTS_DIR / 'recipes.parquet'
INTERACTIONS_PARQUET_PATH = ARTIFACTS_DIR / 'interactions.parquet'
RECIPE_EMBEDDINGS_PATH = ARTIFACTS_DIR / 'recipe_embeddings.npy'
TWO_TOWER_MODEL_PATH = ARTIFACTS_DIR / 'two_tower.pt'

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'recipes_db')
DB_URI = os.getenv(
    'DATABASE_URL',
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
)