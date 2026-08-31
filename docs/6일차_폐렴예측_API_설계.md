# 6일차 폐렴예측 API 설계

## 1. 목표

사용자가 업로드한 흉부 X-Ray 이미지를 AI 모델에 입력하여 폐렴 예측 결과를 응답하고, 저장된 진료기록의 X-Ray 이미지를 바탕으로 예측 결과를 생성 및 조회할 수 있는 API를 설계한다.

이번 API는 다음 요구사항을 기준으로 한다.

- REQ-PRED-001: AI 모델 활용 폐렴 예측
- REQ-PRED-002: AI 모델 활용 폐렴 예측 결과 조회
- NFR-PRED-001: AI 모델 평가 기준
- NFR-PRED-002: API 성능

## 2. 공통 정책

| 항목 | 내용 |
| --- | --- |
| 인증 방식 | JWT Access Token을 `Authorization: Bearer {token}` 형식으로 전달 |
| 접근 가능 유저 | 로그인된 사내 의료인, 개발팀, 연구자 권한 유저 |
| 접근 제한 | 권한이 없는 유저는 `403 Forbidden` |
| 응답 시간 | 모든 API는 3초 이내 응답을 목표로 함 |
| Heatmap Image URL | 선택사항이며, 현재 모델에서 생성하지 않는 경우 `null` 반환 |

## 3. API 목록

| 요구사항 ID | 기능 | Method | Endpoint |
| --- | --- | --- | --- |
| REQ-PRED-001 | 업로드 X-Ray 폐렴 예측 | POST | `/api/v1/predictions/pneumonia` |
| REQ-PRED-001 | 저장된 진료기록 기반 폐렴 예측 | POST | `/api/v1/medical-records/{record_id}/predict` |
| REQ-PRED-002 | AI 모델 활용 폐렴 예측 결과 조회 | GET | `/api/v1/medical-records/{record_id}/analyses` |

## 4. 업로드 X-Ray 폐렴 예측 API

### 기본 정보

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| Endpoint | `/api/v1/predictions/pneumonia` |
| 설명 | 사용자가 업로드한 흉부 X-Ray 이미지를 즉시 AI 모델에 입력하여 폐렴 여부를 예측한다. |
| 인증 | 필요 |

### Request Body

`multipart/form-data` 형식으로 이미지를 업로드한다.

| 이름 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| xray_image | file | 필수 | 폐렴 예측에 사용할 흉부 X-Ray 이미지 |

### 처리 흐름

1. 로그인 유저의 권한을 확인한다.
2. 업로드된 파일이 JPEG 또는 PNG 이미지인지 확인한다.
3. 이미지 파일이 비어 있지 않은지 확인한다.
4. 업로드된 이미지를 AI 모델 입력 형식에 맞게 변환한다.
5. 모델을 활용하여 폐렴 여부와 confidence를 계산한다.
6. 예측 결과를 응답한다.

### Response Body

```json
{
  "is_pneumonia": true,
  "confidence": 92.35,
  "heatmap_url": null,
  "ai_model": "SimpleCNN-sample-v1"
}
```

### 예외 처리

| 상황 | Status Code | 응답 메시지 |
| --- | --- | --- |
| 인증 토큰이 없거나 유효하지 않음 | 401 Unauthorized | 유효하지 않은 토큰입니다. |
| 권한이 없는 유저가 접근 | 403 Forbidden | 진료기록 관리 기능을 사용할 권한이 없습니다. |
| JPEG 또는 PNG가 아닌 파일 업로드 | 422 Unprocessable Entity | 흉부 X-Ray 이미지는 JPEG 또는 PNG 형식만 업로드할 수 있습니다. |
| 비어 있는 파일 업로드 | 422 Unprocessable Entity | 업로드된 이미지 파일이 비어 있습니다. |

## 5. 저장된 진료기록 기반 폐렴 예측 API

### 기본 정보

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| Endpoint | `/api/v1/medical-records/{record_id}/predict` |
| 설명 | 진료기록에 저장된 X-Ray 이미지를 사용하여 폐렴 여부를 예측한다. |
| 인증 | 필요 |

### Path Parameter

| 이름 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| record_id | int | 필수 | 예측을 수행할 진료기록 ID |

### 처리 흐름

1. 로그인 유저의 권한을 확인한다.
2. `record_id`에 해당하는 진료기록을 조회한다.
3. 진료기록에 저장된 X-Ray 이미지가 있는지 확인한다.
4. 같은 진료기록에 대해 같은 모델로 이미 저장된 예측 결과가 있는지 확인한다.
5. 저장된 결과가 있으면 AI 추론을 다시 하지 않고 기존 결과를 반환한다.
6. 저장된 결과가 없으면 X-Ray 이미지를 AI 모델에 입력하여 폐렴 여부와 confidence를 계산한다.
7. 계산된 예측 결과를 `ai_analysis_results` 테이블에 저장한다.
8. 저장된 예측 결과를 응답한다.

### Response Body

```json
{
  "id": 1,
  "record_id": 3,
  "is_pneumonia": true,
  "confidence": 92.35,
  "heatmap_url": null,
  "ai_model": "SimpleCNN-sample-v1",
  "created_at": "2026-08-31T17:00:00"
}
```

### 예외 처리

| 상황 | Status Code | 응답 메시지 |
| --- | --- | --- |
| 인증 토큰이 없거나 유효하지 않음 | 401 Unauthorized | 유효하지 않은 토큰입니다. |
| 권한이 없는 유저가 접근 | 403 Forbidden | 진료기록 관리 기능을 사용할 권한이 없습니다. |
| 진료기록이 존재하지 않음 | 404 Not Found | 진료기록을 찾을 수 없습니다. |
| 예측에 사용할 X-Ray 이미지가 없음 | 404 Not Found | 예측에 사용할 X-Ray 이미지가 없습니다. |
| 저장된 X-Ray 이미지 파일을 찾을 수 없음 | 404 Not Found | 저장된 X-Ray 이미지 파일을 찾을 수 없습니다. |

## 6. AI 모델 활용 폐렴 예측 결과 조회 API

### 기본 정보

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| Endpoint | `/api/v1/medical-records/{record_id}/analyses` |
| 설명 | 특정 진료기록에 저장된 AI 폐렴 예측 결과 목록을 조회한다. |
| 인증 | 필요 |

### Path Parameter

| 이름 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| record_id | int | 필수 | 예측 결과를 조회할 진료기록 ID |

### Response Body

```json
[
  {
    "id": 1,
    "record_id": 3,
    "is_pneumonia": true,
    "confidence": 92.35,
    "heatmap_url": null,
    "ai_model": "SimpleCNN-sample-v1",
    "created_at": "2026-08-31T17:00:00"
  }
]
```

### 조회 가능한 필드

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | int | AI 예측 결과 고유 ID |
| record_id | int | 예측 대상 진료기록 ID |
| is_pneumonia | boolean | 폐렴 여부 |
| confidence | number | 예측 신뢰도 |
| heatmap_url | string or null | 히트맵 이미지 URL |
| ai_model | string | 사용한 AI 모델 |
| created_at | datetime | 예측 수행 일시 |

### 예외 처리

| 상황 | Status Code | 응답 메시지 |
| --- | --- | --- |
| 인증 토큰이 없거나 유효하지 않음 | 401 Unauthorized | 유효하지 않은 토큰입니다. |
| 권한이 없는 유저가 접근 | 403 Forbidden | 진료기록 관리 기능을 사용할 권한이 없습니다. |
| 진료기록이 존재하지 않음 | 404 Not Found | 진료기록을 찾을 수 없습니다. |

## 7. AI 모델 평가 기준

| 지표 | 기준 | 설명 | 계산식 |
| --- | --- | --- | --- |
| Recall | 최소 0.90 이상 | 실제 폐렴 환자를 얼마나 놓치지 않는지 확인하는 핵심 지표 | `TP / (TP + FN)` |
| Accuracy | 0.80 이상 권장 | 전체 예측 중 정답 비율을 확인하는 보조 지표 | `(TP + TN) / 전체 표본 수` |

의료 서비스에서는 폐렴 환자를 정상으로 판단하는 `FN(False Negative)`이 가장 위험하므로, Accuracy보다 Recall을 더 중요하게 본다.

## 8. 구현 파일 계획

| 파일 | 역할 |
| --- | --- |
| `worker/models/model.pth` | 폐렴 예측에 사용할 학습된 모델 파일 |
| `worker/model.py` | 모델을 메모리에 로드하고 이미지 예측을 수행 |
| `app/apis/prediction.py` | 폐렴 예측 API 라우터 |
| `app/services/prediction.py` | 예측 실행, 기존 결과 재사용, 권한 확인 |
| `app/repositories/ai_analysis_result.py` | AI 예측 결과 DB 저장 및 조회 |
| `app/schemas/ai_analysis_result.py` | API 응답 형식 정의 |
| `app/main.py` | 폐렴 예측 API 라우터 등록 |

## 9. Swagger UI 확인 방법

서버 실행 후 `http://127.0.0.1:8000/docs`에 접속하여 다음 API가 보이면 정상이다.

- `POST /api/v1/predictions/pneumonia`
- `POST /api/v1/medical-records/{record_id}/predict`
- `GET /api/v1/medical-records/{record_id}/analyses`
