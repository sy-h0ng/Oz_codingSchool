"""흉부 X-Ray 이미지로 폐렴 여부를 예측하는 AI 모델 워커."""

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
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 학습 당시의 클래스 순서: 0 = 정상, 1 = 폐렴
PNEUMONIA_CLASS_INDEX = 1


class SimpleCNN(nn.Module):
    """model.pth를 학습할 때 사용한 신경망 구조."""

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
        self.fc = nn.Linear(32 * 32 * 32, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = torch.flatten(x, start_dim=1)
        return self.fc(x)


_image_transform = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
    ]
)
_model: nn.Module | None = None


def get_model() -> nn.Module:
    """모델 파일은 처음 한 번만 읽고 이후에는 메모리의 모델을 재사용한다."""

    global _model
    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

    # 받은 pth 파일은 __main__.SimpleCNN으로 저장되어 있다.
    # API 서버에서 import할 때도 읽을 수 있도록 현재 SimpleCNN을 잠시 등록한다.
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
        # 모델 전체가 아니라 state_dict만 저장된 경우도 지원한다.
        state_dict = loaded.get("model_state_dict", loaded)
        model = SimpleCNN()
        model.load_state_dict(state_dict)
    else:
        raise TypeError("지원하지 않는 모델 파일 형식입니다.")

    model.to(DEVICE)
    model.eval()  # 예측할 때는 학습 모드를 끈다.
    _model = model
    return _model


def _open_image(image: bytes | BinaryIO | Path | str) -> Image.Image:
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image)).convert("RGB")
    if isinstance(image, (str, Path)):
        return Image.open(image).convert("RGB")
    return Image.open(image).convert("RGB")


def predict_pneumonia(image: bytes | BinaryIO | Path | str) -> dict[str, bool | float]:
    """이미지 하나를 받아 폐렴 예측 결과를 반환한다.

    반환 예시: {"is_pneumonia": True, "confidence": 92.35}
    """

    model = get_model()
    image_tensor = _image_transform(_open_image(image)).unsqueeze(0).to(DEVICE)

    with torch.inference_mode():
        logits = model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    pneumonia_probability = float(probabilities[PNEUMONIA_CLASS_INDEX].item())
    predicted_class = int(torch.argmax(probabilities).item())
    return {
        "is_pneumonia": predicted_class == PNEUMONIA_CLASS_INDEX,
        "confidence": round(pneumonia_probability * 100, 2),
    }
