import numpy as np
import pandas as pd
import torch

from ml.model import TwoTower


@torch.no_grad()
def generate_recipe_embeddings(model: TwoTower,
                               recipes: pd.DataFrame,
                               device: torch.device,
                               batch_size: int = 2048) -> torch.Tensor:
  model.eval()

  ingredients = recipes['ingredient_ids'].tolist()
  n_recipes = len(ingredients)
  ids = torch.arange(n_recipes, device=device, dtype=torch.int64)
  embeddings: list[torch.Tensor] = []

  for i in range(0, n_recipes, batch_size):
    batch_ids = ids[i : i + batch_size]
    batch_ingredients = ingredients[i : i + batch_size]

    flat_ingredients = torch.tensor(
      [ing for ings in batch_ingredients for ing in ings],
      dtype=torch.int64,
      device=device
    )

    lengths = [len(ings) for ings in batch_ingredients]
    offsets = torch.zeros(len(batch_ids), dtype=torch.int64, device=device)
    offsets[1:] = torch.tensor(
      lengths[:-1], dtype=torch.int64, device=device
    ).cumsum(dim=0)

    batch_embeddings = model.forward_recipe(batch_ids, flat_ingredients, offsets)
    embeddings.append(batch_embeddings)
  return torch.cat(embeddings, dim=0)


@torch.no_grad()
def evaluate_metrics(model: TwoTower,
                     val_interactions: pd.DataFrame,
                     recipes: pd.DataFrame,
                     device: torch.device,
                     k: int = 20,
                     batch_size: int = 2048) -> tuple[float, float]:
  model.eval()

  recipe_embeddings = generate_recipe_embeddings(model, recipes, device, batch_size)

  recipe_sets: list[set[int]] = [set(ings) for ings in recipes['ingredient_ids']]

  val_users = torch.from_numpy(
      val_interactions['user_id'].to_numpy(dtype=np.int64, copy=True)
  ).to(device)
  val_targets = torch.from_numpy(
      val_interactions['recipe_id'].to_numpy(dtype=np.int64, copy=True)
  ).to(device)

  hits = 0
  total_jaccard = 0.0
  total = len(val_interactions)

  for i in range(0, total, batch_size):
    users = val_users[i : i + batch_size]
    targets = val_targets[i : i + batch_size]

    user_embeddings = model.forward_user(users)
    scores = torch.matmul(user_embeddings, recipe_embeddings.T)
    top_indices = torch.topk(scores, k=k, dim=1).indices

    hits += (top_indices == targets.unsqueeze(1)).any(dim=1).sum().item()

    top_indices = top_indices.tolist()
    targets = targets.tolist()

    for target_id, rec_ids in zip(targets, top_indices):
      target = recipe_sets[target_id]

      best_jaccard = 0.0
      for r_id in rec_ids:
        candidate = recipe_sets[r_id]
        intersection = len(target & candidate)
        union = len(target | candidate)
        jaccard = intersection / union
        if jaccard > best_jaccard:
          best_jaccard = jaccard

      total_jaccard += best_jaccard

  recall = hits / total
  mean_jaccard = total_jaccard / total

  return recall, mean_jaccard