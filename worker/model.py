"""Pneumonia prediction worker using the bundled PyTorch model."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import BinaryIO

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

MODEL_PATH = Path(__file__).resolve().parent / "models" / "model.pth"
IMAGE_SIZE = 128
PNEUMONIA_CLASS_INDEX = 1
MODEL_NAME = "SimpleCNN-sample-v1"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SimpleCNN(nn.Module):
    """CNN architecture used when model.pth was trained."""

    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * (IMAGE_SIZE // 4) * (IMAGE_SIZE // 4), 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(self.conv(x))


def _load_model() -> nn.Module:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    main_module = sys.modules["__main__"]
    original_class = getattr(main_module, "SimpleCNN", None)
    setattr(main_module, "SimpleCNN", SimpleCNN)
    try:
        loaded = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
    finally:
        if original_class is None:
            delattr(main_module, "SimpleCNN")
        else:
            setattr(main_module, "SimpleCNN", original_class)

    if isinstance(loaded, nn.Module):
        model = loaded
    elif isinstance(loaded, dict):
        state_dict = loaded.get("model_state_dict", loaded)
        model = SimpleCNN()
        model.load_state_dict(state_dict)
    else:
        raise TypeError("Unsupported model file format.")

    model.to(DEVICE)
    model.eval()
    return model


MODEL = _load_model()


def _open_image(image: bytes | BinaryIO | Path | str) -> Image.Image:
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image)).convert("L")
    if isinstance(image, (str, Path)):
        return Image.open(image).convert("L")
    return Image.open(image).convert("L")


def _preprocess(image: bytes | BinaryIO | Path | str) -> torch.Tensor:
    opened_image = _open_image(image).resize((IMAGE_SIZE, IMAGE_SIZE))
    image_array = np.array(opened_image, dtype=np.float32) / 255.0
    image_tensor = torch.from_numpy(image_array).unsqueeze(0).unsqueeze(0)
    return image_tensor.to(DEVICE)


def predict_pneumonia(image: bytes | BinaryIO | Path | str) -> dict[str, bool | float | str]:
    """Return pneumonia prediction for one uploaded chest X-Ray image."""
    input_tensor = _preprocess(image)

    with torch.inference_mode():
        logits = MODEL(input_tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    predicted_class = int(torch.argmax(probabilities).item())
    pneumonia_probability = float(probabilities[PNEUMONIA_CLASS_INDEX].item())

    return {
        "is_pneumonia": predicted_class == PNEUMONIA_CLASS_INDEX,
        "confidence": round(pneumonia_probability * 100, 2),
        "ai_model": MODEL_NAME,
    }


# Short alias for callers that simply import worker.model.predict.
def predict(image: bytes | BinaryIO | Path | str) -> dict[str, bool | float | str]:
    return predict_pneumonia(image)
