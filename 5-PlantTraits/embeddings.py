"""Compute the DINOv2 embeddings of the PlantTraits photographs.

Run this script from the folder 5-PlantTraits, preferably with a GPU:

    python embeddings.py

The embeddings are saved in the folder data/embeddings, and loaded with load_embeddings from utils.py.
"""

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from utils import EMBEDDINGS_PATH, load_data, load_image

MODEL_NAME = "dinov2_vitl14"
IMAGE_SIZE = 518
BATCH_SIZE = 48
NUM_WORKERS = 8


class PhotoDataset(Dataset):
    """Photographs with the given ids, prepared for DINOv2."""

    transform = transforms.Compose([
        transforms.Resize(IMAGE_SIZE, interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    def __init__(self, image_ids):
        self.image_ids = image_ids

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, index):
        return self.transform(load_image(self.image_ids[index]))


def compute_embeddings(image_ids):
    """Compute the DINOv2 embedding of each photograph."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = torch.hub.load("facebookresearch/dinov2", MODEL_NAME).to(device).eval()
    loader = DataLoader(PhotoDataset(image_ids), batch_size=BATCH_SIZE, num_workers=NUM_WORKERS, pin_memory=device == "cuda")

    embeddings = []
    with torch.inference_mode():
        for batch, images in enumerate(loader, start=1):
            with torch.amp.autocast(device_type=device, enabled=device == "cuda"):
                embeddings.append(model(images.to(device)).float().cpu().numpy())
            if batch % 100 == 0:
                print(f"Batch {batch} of {len(loader)}", flush=True)
    return np.concatenate(embeddings)


if __name__ == "__main__":
    data_df, _, _ = load_data()
    image_ids = data_df["id"].to_numpy()
    embeddings = compute_embeddings(image_ids)

    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez(EMBEDDINGS_PATH, ids=image_ids, embeddings=embeddings)
    print(f"Saved {embeddings.shape[0]} embeddings of size {embeddings.shape[1]} to {EMBEDDINGS_PATH}")
