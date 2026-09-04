"""독립 AI worker가 메모리에 올려 재사용하는 폐렴 예측 모델."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import BinaryIO

import torch
from PIL import Image
from torch import nn
from torchvision import transforms

MODEL_PATH = Path(__file__).resolve().parent / "models" / "model.pth"
DEVICE = torch.device("cpu")
PNEUMONIA_CLASS_INDEX = 1


class SimpleCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.fc = nn.Linear(32 * 32 * 32, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(torch.flatten(self.conv(x), start_dim=1))


_image_transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])
_model: nn.Module | None = None


def get_model() -> nn.Module:
    """worker 기동 뒤 첫 작업에서만 모델 파일을 읽고 이후에는 메모리를 사용한다."""
    global _model
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

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
        model = SimpleCNN()
        model.load_state_dict(loaded.get("model_state_dict", loaded))
    else:
        raise TypeError("지원하지 않는 모델 파일 형식입니다.")

    _model = model.to(DEVICE).eval()
    return _model


def predict_pneumonia(image: bytes | BinaryIO | Path | str) -> dict[str, bool | float]:
    if isinstance(image, bytes):
        opened = Image.open(io.BytesIO(image)).convert("RGB")
    else:
        opened = Image.open(image).convert("RGB")
    image_tensor = _image_transform(opened).unsqueeze(0).to(DEVICE)
    with torch.inference_mode():
        probabilities = torch.softmax(get_model()(image_tensor), dim=1)[0]
    probability = float(probabilities[PNEUMONIA_CLASS_INDEX].item())
    return {
        "is_pneumonia": int(torch.argmax(probabilities).item()) == PNEUMONIA_CLASS_INDEX,
        "confidence": round(probability * 100, 2),
    }
