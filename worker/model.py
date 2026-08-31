from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "model.pth"

IMAGE_SIZE = 128
PNEUMONIA_CLASS_INDEX = 1
MODEL_NAME = "SimpleCNN-sample-v1"


class SimpleCNN(nn.Module):
    """흉부 X-Ray 이미지를 정상/폐렴 2-class로 분류하는 샘플 CNN.

    Stage 6에서 제공된 model.pth는 모델 구조를 포함한 전체 pickle이라,
    역직렬화하려면 저장 당시와 동일한 이름의 클래스가 필요하다. 아래 구조는
    model.pth의 state_dict 텐서 shape((16,1,3,3), (32,16,3,3), (2,32768))를
    역산해 복원한 것이다.
    """

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
        x = self.conv(x)
        x = self.fc(x)
        return x


_model: SimpleCNN | None = None


def get_model() -> SimpleCNN:
    """모델을 최초 호출 시 메모리에 올려두고 이후 호출부터는 재사용한다."""
    global _model
    if _model is None:
        # model.pth는 구조+가중치가 함께 pickle되어 있어, 저장 당시처럼
        # SimpleCNN이 __main__ 모듈에 노출되어 있어야 역직렬화된다.
        import __main__

        __main__.SimpleCNN = SimpleCNN
        model = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        model.eval()
        _model = model
    return _model


def _preprocess(image_bytes: bytes) -> torch.Tensor:
    image = Image.open(io.BytesIO(image_bytes)).convert("L").resize((IMAGE_SIZE, IMAGE_SIZE))
    array = np.array(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array)
    return tensor.unsqueeze(0).unsqueeze(0)  # (batch=1, channel=1, H, W)


def predict(image_bytes: bytes) -> tuple[bool, float]:
    """흉부 X-Ray 이미지 바이트를 입력받아 (폐렴 여부, confidence)를 반환한다."""
    model = get_model()
    input_tensor = _preprocess(image_bytes)
    with torch.no_grad():
        logits = model(input_tensor)
        probabilities = torch.softmax(logits, dim=1)[0]
    predicted_class = int(torch.argmax(probabilities).item())
    confidence = float(probabilities[predicted_class].item())
    is_pneumonia = predicted_class == PNEUMONIA_CLASS_INDEX
    return is_pneumonia, confidence
