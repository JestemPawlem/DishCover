from dataclasses import dataclass, field
import logging
from typing import NamedTuple

import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from src.dataset import TwoTowerCollator, TwoTowerDataset
from src.evaluation import evaluate_metrics
from src.model import TwoTower


logger = logging.getLogger(__name__)


class SplitResult(NamedTuple):
    train: pd.DataFrame
    val: pd.DataFrame

def split_train_val(interactions: pd.DataFrame) -> SplitResult:
    shuffled = interactions.sample(frac=1.0)
    val_mask = ~shuffled.duplicated(subset=['user_id'])
    return SplitResult(
        train=shuffled[~val_mask].reset_index(drop=True),
        val=shuffled[val_mask].reset_index(drop=True)
    )


@dataclass
class TrainingResult:
    model: TwoTower
    best_metrics: dict[str, object]
    history: list[dict[str, object]]
    hyperparameters: dict[str, object] = field(default_factory=dict)

def train_epoch(model: TwoTower,
                loader: DataLoader,
                optimizer: torch.optim.Optimizer,
                device: torch.device,
                temperature: float) -> float:
    model.train()
    total_loss = 0.0

    progress_bar = tqdm(loader, desc='Training', leave=False)
    for users, recipes, ingredients, offsets in progress_bar:
        users = users.to(device)
        recipes = recipes.to(device)
        ingredients = ingredients.to(device)
        offsets = offsets.to(device)

        optimizer.zero_grad()
        users_pred, recipes_pred = model(users, recipes, ingredients, offsets)

        logits = torch.matmul(users_pred, recipes_pred.T) / temperature
        labels = torch.arange(logits.size(0), device=device)

        loss = F.cross_entropy(logits, labels)
        loss.backward()
        optimizer.step()

        loss_val = loss.item()
        total_loss += loss_val
        progress_bar.set_postfix(loss=f'{loss_val:.4f}')

    return total_loss / len(loader)

def train(recipes: pd.DataFrame,
          interactions: pd.DataFrame,
          epochs: int = 30,
          batch_size: int = 2048,
          lr: float = 1e-2,
          embedding_dim: int = 128,
          temperature: float = 0.15,
          eval_k: int = 20) -> TrainingResult:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info('Training on device: %s', device)

    train_interactions, val_interactions = split_train_val(interactions)
    logger.info('Train interactions: %d | Val interactions: %d',
                len(train_interactions), len(val_interactions))

    dataset = TwoTowerDataset(train_interactions)
    collator = TwoTowerCollator(recipes)

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collator
    )

    model = TwoTower(
        n_users=interactions['user_id'].nunique(),
        n_recipes=len(recipes),
        n_canonicals=int(collator.ingredients.max().item()) + 1,
        embedding_dim=embedding_dim
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_jaccard = -1.0
    best_recall = 0.0
    best_epoch = 0
    best_weights = None
    history: list[dict[str, object]] = []

    for epoch in range(epochs):
        mean_loss = train_epoch(model, loader, optimizer, device, temperature)
        val_recall, val_jaccard = evaluate_metrics(
            model, val_interactions, recipes, device, eval_k
        )

        logger.info('Epoch %02d/%02d | Loss: %.4f | Recall@%d: %.4f | Jaccard@%d: %.4f',
                    epoch + 1, epochs, mean_loss, eval_k, val_recall, eval_k, val_jaccard)

        if val_jaccard > best_jaccard:
            best_jaccard = val_jaccard
            best_recall = val_recall
            best_epoch = epoch + 1
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        history.append({
            'epoch': epoch + 1,
            'train_loss': round(mean_loss, 4),
            f'val_recall_{eval_k}': round(val_recall, 4),
            f'val_jaccard_{eval_k}': round(val_jaccard, 4),
        })

    if best_weights is not None:
        model.load_state_dict(best_weights)
        logger.info('Restored best weights from epoch %d (Jaccard: %.4f)',
            best_epoch, best_jaccard)

    return TrainingResult(
        model=model,
        best_metrics={
            'best_epoch': best_epoch,
            f'val_recall_{eval_k}': round(best_recall, 4),
            f'val_jaccard_{eval_k}': round(best_jaccard, 4),
        },
        history=history,
        hyperparameters={
            'epochs': epochs,
            'batch_size': batch_size,
            'lr': lr,
            'embedding_dim': embedding_dim,
            'temperature': temperature,
            'eval_k': eval_k,
        },
    )