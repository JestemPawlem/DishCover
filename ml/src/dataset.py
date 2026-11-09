import numpy as np
import pandas as pd
import torch
from torch import Tensor
from torch.utils.data import Dataset


class TwoTowerDataset(Dataset):

    def __init__(self,
                 interactions: pd.DataFrame):
        self.user_indices = interactions['user_id'].to_numpy(dtype=np.int64)
        self.recipe_indices = interactions['recipe_id'].to_numpy(dtype=np.int64)

    def __len__(self) -> int:
        return len(self.user_indices)

    def __getitem__(self,
                    idx: int) -> tuple[int, int]:
        return self.user_indices[idx], self.recipe_indices[idx]


class TwoTowerCollator:

    def __init__(self,
                 recipes: pd.DataFrame):
        n_recipes = len(recipes)

        recipes = recipes.sort_values('id')
        ingredient_ids = recipes['ingredient_ids'].to_list()

        max_ingredients = max(len(ings) for ings in ingredient_ids)

        ingredients = np.zeros((n_recipes, max_ingredients), dtype=np.int64)
        lengths = np.zeros(n_recipes, dtype=np.int64)

        for recipe_idx, ings in enumerate(ingredient_ids):
            ingredients[recipe_idx, :len(ings)] = ings
            lengths[recipe_idx] = len(ings)

        self.ingredients = torch.from_numpy(ingredients)
        self.lengths = torch.from_numpy(lengths)

    def __call__(self,
                 batch: list[tuple[int, int]]) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        batch_tensor = torch.as_tensor(batch, dtype=torch.long)
        user_ids, recipe_ids = batch_tensor[:, 0], batch_tensor[:, 1]

        ingredients = self.ingredients[recipe_ids]
        lengths = self.lengths[recipe_ids]

        max_len = ingredients.size(1)
        mask = torch.arange(max_len).unsqueeze(0) < lengths.unsqueeze(1)
        flat_ingredients = ingredients[mask]

        offsets = torch.zeros(len(recipe_ids), dtype=torch.long)
        offsets[1:] = torch.cumsum(lengths[:-1], dim=0)

        return user_ids, recipe_ids, flat_ingredients, offsets