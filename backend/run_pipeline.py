import os
import kagglehub
import pandas as pd
from ml.preprocessing import preprocess
from ml.training import train

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')


def main():
    print('1/4 Downloading dataset...')
    path = kagglehub.dataset_download('shuyangli94/food-com-recipes-and-user-interactions')

    print("2/4 Loading CSV files...")
    recipes = pd.read_csv(os.path.join(path, 'RAW_recipes.csv'))
    interactions = pd.read_csv(os.path.join(path, 'RAW_interactions.csv'))

    print('3/4 Preprocessing and saving artifacts...')
    data = preprocess(recipes=recipes, interactions=interactions)
    data.save_artifacts(output_dir=ARTIFACTS_DIR)

    print('4/4 Training model...')
    train(
        interactions=data.interactions,
        recipes=data.recipes,
        output_dir=ARTIFACTS_DIR
    )

    print(f'\nPipeline finished successfully. All artifacts saved to: {ARTIFACTS_DIR}')


if __name__ == '__main__':
    main()