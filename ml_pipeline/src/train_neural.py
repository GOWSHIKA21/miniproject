"""PyTorch Deep Learning Multi-Class Neural Text Classifier.
Builds, trains, and validates a deep neural network on patent textual representations.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, f1_score

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class SparseDataset(Dataset):
    """PyTorch Dataset wrapping sparse TF-IDF matrices."""
    def __init__(self, X_sparse, y_labels):
        self.X = X_sparse
        self.y = torch.tensor(y_labels, dtype=torch.long)

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        # Convert row slice to dense tensor
        x_dense = torch.tensor(self.X[idx].toarray().squeeze(), dtype=torch.float32)
        return x_dense, self.y[idx]


class PatentMLPClassifier(nn.Module):
    """Deep Multi-Layer Perceptron for Patent Domain Classification."""
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int, dropout_rate: float = 0.3):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate / 1.5),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, x):
        return self.network(x)


def train_neural_network(
    feature_data: Dict[str, Any],
    epochs: int = config.NEURAL_EPOCHS,
    batch_size: int = config.NEURAL_BATCH_SIZE,
    learning_rate: float = config.NEURAL_LR
) -> Dict[str, Any]:
    """Train PyTorch neural network classifier and save model weights."""
    X_train = feature_data["X_train_tfidf"]
    y_train = feature_data["y_train"]
    X_val = feature_data["X_val_tfidf"]
    y_val = feature_data["y_val"]
    X_test = feature_data["X_test_tfidf"]
    y_test = feature_data["y_test"]
    classes = feature_data["classes"]

    input_dim = X_train.shape[1]
    num_classes = len(classes)

    logger.info(f"Initializing PyTorch PatentMLPClassifier (input_dim={input_dim}, classes={num_classes})...")

    # Limit training subset if very large for fast training convergence
    max_train_samples = min(20000, X_train.shape[0])
    max_val_samples = min(5000, X_val.shape[0])

    train_dataset = SparseDataset(X_train[:max_train_samples], y_train[:max_train_samples])
    val_dataset = SparseDataset(X_val[:max_val_samples], y_val[:max_val_samples])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    model = PatentMLPClassifier(
        input_dim=input_dim,
        hidden_dim=config.NEURAL_HIDDEN_DIM,
        num_classes=num_classes,
        dropout_rate=config.NEURAL_DROPOUT
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=1)

    history = {
        "train_loss": [],
        "val_accuracy": [],
        "val_f1": []
    }

    best_val_acc = 0.0

    logger.info(f"Beginning neural training for {epochs} epochs...")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * batch_x.size(0)

        epoch_loss = running_loss / len(train_dataset)

        # Validation evaluation
        model.eval()
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(device)
                outputs = model(batch_x)
                preds = torch.argmax(outputs, dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_targets.extend(batch_y.numpy())

        val_acc = float(accuracy_score(all_targets, all_preds))
        val_f1 = float(f1_score(all_targets, all_preds, average="weighted"))

        scheduler.step(val_acc)

        history["train_loss"].append(round(epoch_loss, 4))
        history["val_accuracy"].append(round(val_acc, 4))
        history["val_f1"].append(round(val_f1, 4))

        logger.info(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_loss:.4f} | Val Acc: {val_acc:.4f} | Val F1: {val_f1:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), config.NEURAL_CLASSIFIER_PATH)

    total_training_time = time.time() - start_time
    logger.info(f"Neural training finished in {total_training_time:.2f}s. Best Val Acc: {best_val_acc:.4f}")
    logger.info(f"Saved PyTorch weights to {config.NEURAL_CLASSIFIER_PATH}")

    # Evaluate on Test Split
    max_test_samples = min(5000, X_test.shape[0])
    test_dataset = SparseDataset(X_test[:max_test_samples], y_test[:max_test_samples])
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    model.load_state_dict(torch.load(config.NEURAL_CLASSIFIER_PATH))
    model.eval()
    test_preds = []
    test_targets = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            outputs = model(batch_x)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            test_preds.extend(preds)
            test_targets.extend(batch_y.numpy())

    test_acc = float(accuracy_score(test_targets, test_preds))
    test_f1 = float(f1_score(test_targets, test_preds, average="weighted"))

    logger.info(f"PyTorch Test Acc: {test_acc:.4f} | Test F1: {test_f1:.4f}")

    training_summary = {
        "model_architecture": "PatentMLPClassifier (BatchNorm + ReLU + Dropout)",
        "input_dim": input_dim,
        "hidden_dim": config.NEURAL_HIDDEN_DIM,
        "epochs": epochs,
        "best_val_accuracy": round(best_val_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "test_f1_score": round(test_f1, 4),
        "training_time_seconds": round(total_training_time, 2),
        "history": history
    }

    history_path = config.REPORTS_DIR / "neural_training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_summary, f, indent=2)
    logger.info(f"Saved neural training history to {history_path}")

    return training_summary


if __name__ == "__main__":
    from feature_engineering import prepare_features_and_splits
    features = prepare_features_and_splits(sample_limit=15000)
    train_neural_network(features, epochs=5)
