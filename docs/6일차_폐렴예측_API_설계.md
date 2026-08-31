# 6일차 AI 폐렴 예측 API 설계

## 1. 개요

요구사항 정의서(REQ-PRED-001~002, NFR-PRED-001~002)와 `main`에 이미 merge된 `app/models/ai_analysis_result.py`, `app/models/medical_record.py`, `app/models/xray_image.py`, 그리고 5일차에 구현된 진료기록 API(`app/services/medical_record.py`)를 기준으로 설계했다.

### 1.1 사용 모델: Stage 6 제공 샘플 모델

이번 과제는 원래 "인공지능 트랙 과제에서 각자 구축한 모델 중 팀 내 상의로 하나를 선택"하는 것이 기본이지만, 아직 팀 내 모델 선정 논의가 되지 않아 **Stage 6 페이지에 첨부된 샘플 모델(`model.pth`)을 우선 사용**했다. 팀에서 실제 학습 모델을 정하면 `worker/models/model.pth`만 교체하고, 구조가 다르면 `worker/model.py`의 `SimpleCNN` 클래스와 전처리(`_preprocess`)만 맞춰 고치면 된다.

`model.pth`는 구조+가중치가 함께 저장된 전체 모델 pickle이라, `state_dict`의 텐서 shape을 역산해 구조를 복원했다.

```
SimpleCNN(
  conv: Conv2d(1,16,3,pad=1) → ReLU → MaxPool2d(2) → Conv2d(16,32,3,pad=1) → ReLU → MaxPool2d(2)
  fc:   Flatten → Linear(32*32*32=32768, 2)
)
```

- 입력: 흉부 X-Ray를 **그레이스케일 128×128**로 리사이즈, `0~1`로 정규화(`/255.0`)한 텐서 `(1, 1, 128, 128)`.
- 출력: 2-class logit → `softmax` → `argmax`. **클래스 인덱스 1 = 폐렴(pneumonia)** 으로 가정했다 (샘플 모델에 클래스 라벨 매핑 문서가 없어, 이진분류 관례상 널리 쓰이는 순서를 채택 — 실제 학습 모델로 교체 시 검증 필요).
- `confidence`는 예측된 클래스의 softmax 확률 값을 `%`(0~100, 소수 2자리)로 변환해 저장한다 (`ai_analysis_results.confidence`가 `Numeric(5,2)` + "확률, %" 코멘트이기 때문).

### 1.2 히트맵(heatmap_url)은 이번 범위에서 비워둔다

요구사항상 `Hitmap Image URL`은 **선택사항**이다. Grad-CAM 등 시각화는 구현하지 않았고, DB 컬럼이 `NOT NULL`이라 빈 문자열(`""`)을 저장한다. 추후 필요 시 `worker/model.py`에 히트맵 생성 로직을 추가하고 `heatmap_url`을 채우면 된다.

### 1.3 캐싱 동작 (REQ-PRED-001)

"이미 해당 진료기록으로 같은 모델을 사용한 예측 결과가 있으면 재추론하지 않는다"는 요구사항에 따라, `(record_id, ai_model)` 조합으로 기존 `ai_analysis_results` row가 있는지 먼저 조회하고 있으면 그대로 반환한다. 모델을 바꿔서 다시 예측하면(=`ai_model` 값이 다르면) 새 row가 추가된다.

### 1.4 사용하는 X-Ray 이미지

"폐렴 예측 시 필요한 X-Ray 이미지는 진료기록 저장 시 업로드한 이미지를 활용한다"는 요구사항에 따라, 해당 진료기록에 연결된 `xray_images` 중 **가장 최근(id가 가장 큰) 이미지**를 사용한다 (5일차 진료기록 상세 조회의 "최신 이미지" 규칙과 동일).

### 1.5 권한

요구사항 문구("사내 의료인, 개발팀, 연구자 권한을 가진 유저")는 5일차 진료기록 API와 동일한 표현이라, 5일차에 이미 구현된 `require_medical_record_access`(`STAFF`, `ADMIN` 허용, `PENDING` 차단)를 그대로 재사용한다.

---

## 2. API 목록

| 요구사항 ID | 기능 | Method | Endpoint | 인증 | 권한 |
| --- | --- | --- | --- | --- | --- |
| REQ-PRED-001 | AI 모델 활용 폐렴 예측 | `POST` | `/medical-records/{record_id}/predict` | 필요 | `STAFF`, `ADMIN` |
| REQ-PRED-002 | AI 예측 결과 목록 조회 | `GET` | `/medical-records/{record_id}/analyses` | 필요 | `STAFF`, `ADMIN` |

## 3. API 상세 명세

### 3.1 AI 모델 활용 폐렴 예측 — `REQ-PRED-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/medical-records/{record_id}/predict` |
| 인증 | 필요 |
| Request Body | 없음 (경로의 `record_id`에 연결된 최신 X-Ray 이미지를 사용) |

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 83.99,
  "heatmap_url": "",
  "ai_model": "SimpleCNN-sample-v1",
  "created_at": "2026-08-31T06:30:03"
}
```

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 예측 성공 (신규 추론 또는 캐시된 기존 결과) |
| `404 Not Found` | 진료기록이 존재하지 않는 경우 |
| `422 Unprocessable Entity` | 진료기록에 연결된 X-Ray 이미지가 없는 경우 |

### 3.2 AI 예측 결과 목록 조회 — `REQ-PRED-002`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/medical-records/{record_id}/analyses` |
| 인증 | 필요 |

응답: 배열, 각 항목은 `id`(고유 ID), `record_id`, `is_pneumonia`(폐렴 여부), `confidence`, `heatmap_url`, `ai_model`(사용한 모델), `created_at`(예측 수행 일시) 포함. 최신순으로 정렬한다.

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 조회 성공 (결과가 없으면 빈 배열) |
| `404 Not Found` | 진료기록이 존재하지 않는 경우 |

## 4. 비기능 요구사항

| 항목 | 내용 |
| --- | --- |
| NFR-PRED-001 | 모델 평가 기준(Recall ≥ 0.90, Accuracy ≥ 0.80)은 실제 학습 모델 선정/평가 단계에서 검증할 항목이며, 현재는 제공된 샘플 모델을 그대로 사용해 API 파이프라인만 검증했다. |
| NFR-PRED-002 | 모든 API는 3초 이내 응답. 샘플 모델은 CPU 추론 기준 수십 ms 수준이라 여유 있게 충족한다. |

## 5. 파일/디렉터리 구조

```
worker/
  model.py          # SimpleCNN 정의, get_model()(lazy singleton 로딩), predict(image_bytes)
  models/
    model.pth              # 모델 구조+가중치 (사용)
    model_state_dict.pth   # 가중치만 (참고용, 현재 미사용)

app/
  models/ai_analysis_result.py    # 기존 (main에 이미 존재)
  schemas/ai_analysis_result.py   # AIAnalysisResultResponse
  repositories/ai_analysis_result.py
  services/ai_analysis_result.py  # require_medical_record_access 재사용, 캐싱 로직
  apis/ai_analysis_result.py      # POST .../predict, GET .../analyses
```

## 6. 남은 과제

- 실제 학습된 모델로 교체 시 클래스 인덱스(정상/폐렴) 매핑 재검증 필요.
- 히트맵(Grad-CAM) 시각화 미구현.
- `feat/patient-apis`, `feature/medical-record-api`처럼 이 기능도 팀 전체가 코드를 이해할 것 (완료 조건).
