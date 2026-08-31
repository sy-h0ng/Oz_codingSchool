from io import BytesIO
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

MODEL_PATH = Path(__file__).resolve().parent / "models" / "model_state_dict.pth"
IMAGE_SIZE = 128
MODEL_NAME = "simple-cnn-v1"  # ai_analysis_results.ai_model에 저장되는 값. 캐시 판단 기준이기도 하다.


class SimpleCNN(nn.Module):
    """흉부 X-Ray 폐렴 판독용 CNN.

    model_state_dict.pth의 레이어 구조(conv.0/3, fc.1)를 그대로 재현한 것이다.
    구조를 바꾸면 저장된 파라미터와 shape이 안 맞아 로드가 실패한다.
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
        return self.fc(x)


# 모델은 이 모듈이 처음 import되는 시점에 딱 한 번만 메모리에 올라간다.
# (요청마다 새로 로드하면 느리고 메모리 낭비가 커서, 워커 프로세스 시작 시 1회만 로드)
_model = SimpleCNN()
_model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
_model.eval()


def _preprocess(image_bytes: bytes) -> torch.Tensor:
    """업로드된 이미지 바이트를 모델 입력 텐서 (1, 1, 128, 128)로 변환한다."""
    image = Image.open(BytesIO(image_bytes)).convert("L")  # 흑백(1채널)으로 변환
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    array = np.asarray(image, dtype=np.float32) / 255.0  # 0~1 범위로 정규화
    tensor = torch.from_numpy(array).unsqueeze(0).unsqueeze(0)  # (H,W) -> (1,1,H,W)
    return tensor


def predict_pneumonia(image_bytes: bytes) -> tuple[bool, float]:
    """흉부 X-Ray 이미지 바이트를 받아 (폐렴 여부, confidence(%))를 반환한다.

    모델 출력은 [정상 클래스, 폐렴 클래스] 순서의 logit 2개이며,
    index 1을 폐렴 클래스로 가정한다 (모델 원저작자 확인 전까지의 가정).
    """
    tensor = _preprocess(image_bytes)
    with torch.no_grad():
        logits = _model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]

    is_pneumonia = bool(torch.argmax(probabilities).item() == 1)
    confidence = round(float(probabilities.max().item()) * 100, 2)
    return is_pneumonia, confidence
