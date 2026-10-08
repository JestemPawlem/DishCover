import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
import os
import pickle
import re

import nltk
from nltk.stem import WordNetLemmatizer
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize


def get_nlp_resources(cache_dir: str = 'artifacts') -> tuple[WordNetLemmatizer, SentenceTransformer]:
    os.makedirs(cache_dir, exist_ok=True)

    nltk_data_dir = os.path.join(cache_dir, 'nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)

    try:
        nltk.data.find('corpora/wordnet', paths=[nltk_data_dir])
    except LookupError:
        nltk.download('wordnet', download_dir=nltk_data_dir, quiet=True)

    lemmatizer = WordNetLemmatizer()

    st_path = os.path.join(cache_dir, 'sentence_transformer')
    if os.path.exists(st_path):
        embedder = SentenceTransformer(st_path)
    else:
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        embedder.save(st_path)

    return lemmatizer, embedder


def clean_ingredient(ingredient: str,
                     lemmatizer: WordNetLemmatizer) -> str:
    ingredient = ingredient.lower().strip()
    ingredient = re.sub(r'\d+', '', ingredient)
    ingredient = re.sub(r'[^\w\s]', '', ingredient)
    return ' '.join(lemmatizer.lemmatize(word, pos='n') for word in ingredient.split())


def eval_list(val: object) -> list[str]:
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, SyntaxError):
            return []
    return val if isinstance(val, list) else []


class IngredientTransformer:

    def __init__(self,
                 ingredient_to_idx: dict[str, int]):
        self.ingredient_to_idx = ingredient_to_idx

    def transform_single(self,
                         ingredient: str) -> int | None:
        cleaned = clean_ingredient(ingredient)
        return self.ingredient_to_idx.get(cleaned)

    def transform_list(self,
                       ingredients: list[str]) -> list[int]:
        return list({
            idx for ingredient in ingredients
            if (idx := self.transform_single(ingredient)) is not None
        })


def cluster_ingredients(ingredients: list[str],
                        embedder: SentenceTransformer,
                        distance_threshold: float = 0.15) -> dict[str, int]:
    embeddings = embedder.encode(ingredients)
    embeddings = normalize(embeddings, norm='l2')

    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='cosine',
        linkage='complete',
        distance_threshold=distance_threshold
    )
    labels = clustering.fit_predict(embeddings)

    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(ingredients[idx])

    canonical_clusters = {}

    for members in clusters.values():
        members.sort(key=lambda x: (len(x), x))
        canonical = members[0]
        canonical_clusters[canonical] = members

    canonical_to_idx = {
        canonical: idx for idx, canonical in enumerate(sorted(canonical_clusters.keys()))
    }

    return {
        member: canonical_to_idx[canonical]
        for canonical, members in canonical_clusters.items()
        for member in members
    }


@dataclass
class PreprocessedData:
    recipes: pd.DataFrame
    interactions: pd.DataFrame
    ingredient_to_idx: dict[str, int]

    def save_artifacts(self,
                       output_dir: str = 'artifacts') -> None:
        os.makedirs(output_dir, exist_ok=True)

        transformer = IngredientTransformer(self.ingredient_to_idx)

        with open(os.path.join(output_dir, 'transformer.pkl'), 'wb') as f:
            pickle.dump(transformer, f)

        with open(os.path.join(output_dir, 'ingredient_to_idx.pkl'), 'wb') as f:
            pickle.dump(self.ingredient_to_idx, f)

        self.recipes.to_parquet(os.path.join(output_dir, 'recipes.parquet'), index=False)
        self.interactions.to_parquet(os.path.join(output_dir, 'interactions.parquet'), index=False)


def preprocess(recipes: pd.DataFrame,
               interactions: pd.DataFrame,
               min_ingredient_count: int,
               min_user_interactions: int,
               min_recipe_interactions: int,
               artifacts_dir: str = 'artifacts') -> PreprocessedData:
    lemmatizer, embedder = get_nlp_resources(cache_dir=artifacts_dir)

    recipes = recipes[['id', 'name', 'minutes', 'description', 'ingredients', 'steps']]
    recipes['ingredients'] = recipes['ingredients'].apply(eval_list)
    recipes['steps'] = recipes['steps'].apply(eval_list)
    recipes['description'] = recipes['description'].fillna('')
    recipes = recipes[(recipes['minutes'] > 0) & (recipes['minutes'] <= 4320)]

    recipes['cleaned_ingredients'] = recipes['ingredients'].apply(
        lambda ings: list({cleaned for ing in ings if (cleaned := clean_ingredient(ing, lemmatizer))})
    )

    freq = Counter(ing for ings in recipes['cleaned_ingredients'] for ing in ings)
    frequent = {ing for ing, count in freq.items() if count >= min_ingredient_count}

    recipes['cleaned_ingredients'] = recipes['cleaned_ingredients'].apply(
        lambda ings: [ing for ing in ings if ing in frequent]
    )
    recipes = recipes[recipes['cleaned_ingredients'].map(len) >= 3]


    interactions = interactions[interactions['rating'] >= 4]
    interactions = interactions[['recipe_id', 'user_id']]

    popular_recipes = (interactions['recipe_id'].value_counts()[lambda x: x >= min_recipe_interactions].index)
    interactions = interactions[interactions['recipe_id'].isin(popular_recipes)]

    active_users = (interactions['user_id'].value_counts()[lambda x: x >= min_user_interactions].index)
    interactions = interactions[interactions['user_id'].isin(active_users)]

    interactions = interactions.merge(
        recipes[['id']], left_on='recipe_id', right_on='id', how='inner'
    )[['user_id', 'recipe_id']]

    surviving_recipe_ids = interactions['recipe_id'].unique()
    recipes = recipes[recipes['id'].isin(surviving_recipe_ids)]

    ingredients = list({ing for ings in recipes['cleaned_ingredients'] for ing in ings})
    ingredient_to_idx = cluster_ingredients(
        ingredients,
        embedder=embedder,
        distance_threshold=0.15
    )

    recipes['ingredient_ids'] = recipes['cleaned_ingredients'].apply(
        lambda ings: list({ingredient_to_idx[ing] for ing in ings})
    )

    interactions['user_id'], _ = pd.factorize(interactions['user_id'])
    interactions['recipe_id'], unique_recipes = pd.factorize(interactions['recipe_id'])

    recipe_map = {old_id: new_id for new_id, old_id in enumerate(unique_recipes)}
    recipes['id'] = recipes['id'].map(recipe_map)
    recipes['id'] = recipes['id'].astype(np.int64)
    recipes = recipes.sort_values('id').reset_index(drop=True)
    recipes.drop(columns=['cleaned_ingredients'], inplace=True)

    return PreprocessedData(
        interactions=interactions.astype(np.int64),
        recipes=recipes,
        ingredient_to_idx=ingredient_to_idx
    )