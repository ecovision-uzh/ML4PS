"""Helpers for the PlantTraits project: dataset paths, column names, data loading and visualization."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset

# Location of the dataset ("train" is the name given by Kaggle: these files are our whole dataset)
DATA_DIR = Path(__file__).parent / "data" / "planttraits2024"
TABLE_PATH = DATA_DIR / "train.csv"
IMAGES_DIR = DATA_DIR / "train_images"

# Precomputed DINOv2 embeddings of the photographs (see embeddings.py)
EMBEDDINGS_PATH = Path(__file__).parent / "data" / "embeddings" / "dinov2_vitl14_518.npz"

# Names of the columns
TARGET_COLS = ["X4_mean", "X11_mean", "X18_mean", "X26_mean", "X50_mean", "X3112_mean"]
FEATURE_GROUPS = ("WORLDCLIM", "SOIL", "MODIS", "VOD")


def load_data():
    """Load the dataset table, and return it with the names of the target and input columns."""
    assert TABLE_PATH.exists(), f"{TABLE_PATH} not found, see 'Data download' in the notebook"
    data_df = pd.read_csv(TABLE_PATH)
    feature_cols = [col for col in data_df.columns if col.startswith(FEATURE_GROUPS)]

    image_ids = {int(path.stem) for path in IMAGES_DIR.glob("*.jpeg")}
    n_missing = len(set(data_df["id"]) - image_ids)
    print(f"{len(data_df)} samples, {len(feature_cols)} input columns, {len(TARGET_COLS)} targets")
    print(f"{n_missing} samples without an image")
    return data_df, TARGET_COLS, feature_cols


def load_image(image_id):
    """Load the photograph with the given id as an RGB image."""
    return Image.open(IMAGES_DIR / f"{int(image_id)}.jpeg").convert("RGB")


def load_embeddings(df):
    """Load the DINOv2 embeddings of the photographs, in the same order as the rows of a table."""
    assert EMBEDDINGS_PATH.exists(), f"{EMBEDDINGS_PATH} not found, put the shared embeddings file at this location"
    saved = np.load(EMBEDDINGS_PATH)
    positions = pd.Series(np.arange(len(saved["ids"])), index=saved["ids"])
    return saved["embeddings"][positions.loc[df["id"]].to_numpy()]


class PlantDataset(Dataset):
    """Photographs, tabular inputs and targets of some samples, to train a neural network with PyTorch.

    Each item is a tuple (photograph prepared with the transform, tabular inputs, targets). The class is defined here,
    and not in the notebook, so that a DataLoader can load the photographs in parallel on all systems.
    """

    def __init__(self, image_ids, tabular, targets, transform):
        self.image_ids = np.asarray(image_ids)
        self.tabular = np.asarray(tabular, dtype=np.float32)
        self.targets = np.asarray(targets, dtype=np.float32)
        self.transform = transform

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, index):
        return self.transform(load_image(self.image_ids[index])), self.tabular[index], self.targets[index]


def show_samples(df, n_images=8, random_state=None):
    """Show random photographs from a table, with their target values as titles."""
    samples = df.sample(n_images, random_state=random_state)

    n_rows = (n_images + 3) // 4
    fig, axes = plt.subplots(n_rows, 4, figsize=(14, 4.5 * n_rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, (_, row) in zip(axes.flat, samples.iterrows()):
        ax.imshow(load_image(row["id"]))
        ax.set_title("\n".join(f"{col}: {row[col]:.4g}" for col in TARGET_COLS), fontsize=9)
    plt.tight_layout()
    plt.show()


def show_sample(row, feature_cols=None):
    """Show one photograph next to its target values and input columns (climate by default)."""
    if feature_cols is None:
        feature_cols = [col for col in row.index if col.startswith("WORLDCLIM")]

    width = max(len(col) for col in [*TARGET_COLS, *feature_cols])
    lines = ["Targets"]
    lines += [f"  {col:<{width}}  {row[col]:.4g}" for col in TARGET_COLS]
    lines += ["", "Environmental data"]
    lines += [f"  {col:<{width}}  {row[col]:.4g}" for col in feature_cols]

    fig, (ax_image, ax_text) = plt.subplots(1, 2, figsize=(14, 6))
    ax_image.imshow(load_image(row["id"]))
    ax_image.set_title(f"Image {int(row['id'])}")
    ax_image.axis("off")
    ax_text.text(0, 0.95, "\n".join(lines), family="monospace", fontsize=9, va="top")
    ax_text.axis("off")
    plt.tight_layout()
    plt.show()
