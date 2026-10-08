import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class TwoTower(nn.Module):

    def __init__(self,
                 n_users: int,
                 n_recipes: int,
                 n_canonicals: int,
                 embedding_dim: int = 128):
        super().__init__()

        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.recipe_embedding = nn.Embedding(n_recipes, embedding_dim)
        self.ingredient_embedding = nn.EmbeddingBag(n_canonicals, embedding_dim, mode='mean')

        self.user_projection = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)
        )
        self.item_projection = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)
        )

    def forward_user(self,
                     user_ids: torch.Tensor) -> torch.Tensor:
        user_embedding = self.user_embedding(user_ids)
        user = self.user_projection(user_embedding)
        return F.normalize(user, p=2, dim=-1)

    def forward_recipe(self,
                       recipe_ids: torch.Tensor,
                       ingredients: torch.Tensor,
                       offsets: torch.Tensor) -> torch.Tensor:
        recipe_embedding = self.recipe_embedding(recipe_ids)

        if self.training:
            mask = (torch.rand(recipe_embedding.size(0), 1, device=recipe_ids.device) > 0.4).float()
            recipe_embedding = recipe_embedding * mask
    
        ingredient_embedding = self.ingredient_embedding(ingredients, offsets)
        concat = torch.cat([recipe_embedding, ingredient_embedding], dim=-1)
        item = self.item_projection(concat)
        return F.normalize(item, p=2, dim=-1)

    def forward(self,
                user_ids: torch.Tensor,
                recipe_ids: torch.Tensor,
                ingredients: torch.Tensor,
                offsets: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        user = self.forward_user(user_ids)
        item = self.forward_recipe(recipe_ids, ingredients, offsets)
        return user, item