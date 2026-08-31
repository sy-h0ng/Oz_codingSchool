# 6일차 폐렴 예측 API 설계

## 1. 개요

요구사항 정의서(REQ-PRED-001~002, NFR-PRED-001~002)와 실제 `main`에 merge된 `app/models/ai_analysis_result.py`, `worker/model.py`(6일차-1에서 작성)를 기준으로 설계했다.

### 1.1 지금 단계에서는 워커를 직접 호출한다 (Redis 큐 아님)

9~10일차에 가서야 Redis 작업 큐 + 별도 AI 워커 프로세스로 분리한다. **지금(6일차) 단계에서는 API가 `worker/model.py`의 `predict_pneumonia()`를 같은 프로세스 안에서 직접 호출**한다. 나중에 9~10일차에서 이 호출 부분만 "Redis에 작업 등록 → 워커가 처리 → 결과 publish" 구조로 교체하게 될 것이다. 지금 짜는 서비스 함수 시그니처를 나중에 그대로 재사용할 수 있도록, 실제 추론 호출 부분을 서비스 계층에 한 군데로 모아둔다.

### 1.2 중요: `heatmap_url`이 요구사항과 DB가 서로 다르다

- 요구사항(REQ-PRED-001): "Hitmap Image URL **(선택사항)**"
- 실제 DB(`ai_analysis_results.heatmap_url`): `nullable=False` — **필수값**

우리 모델(`SimpleCNN`)은 Grad-CAM 같은 히트맵 생성 기능이 없다 (단순 CNN이라 "어느 부위를 보고 판단했는지" 시각화를 안 만듦). 그런데 DB는 값을 필수로 요구한다.

**해결**: 히트맵을 실제로 생성하는 대신, **원본 X-Ray 이미지 URL을 그대로 `heatmap_url`에 저장**한다. 진짜 히트맵이 아니라는 점을 코드 주석과 이 문서에 명시해서, 나중에 실제 히트맵 생성 기능이 추가되면 이 부분만 교체하면 되게 한다.

### 1.3 캐싱 조건의 "동일 모델" 판단 기준

`worker/model.py`에 `MODEL_NAME = "simple-cnn-v1"` 상수를 정의하고, `ai_analysis_results.ai_model`에 저장할 때도 이 값을 쓴다. 캐시 확인 시 `record_id`와 `ai_model`이 둘 다 일치하는 기존 결과가 있는지로 판단한다.

---

## 2. API 명세

### 2.1 AI 폐렴 예측 수행 — `REQ-PRED-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/medical-records/{record_id}/predict` |
| 인증 | 필요 (STAFF 이상 — PENDING 접근 불가, 공통 규칙과 동일) |
| Request Body | 없음 |

**처리 순서**:
1. `record_id`로 진료기록 존재 확인 (없으면 404)
2. 해당 `record_id` + `ai_model="simple-cnn-v1"` 조합으로 **이미 저장된 예측 결과가 있는지 확인** → 있으면 바로 그 결과를 응답으로 반환하고 끝 (재추론 안 함)
3. 없으면: 진료기록에 연결된 X-Ray 이미지 파일을 로컬 저장소에서 읽음
4. `worker.model.predict_pneumonia(image_bytes)` 호출 → `(is_pneumonia, confidence)` 받음
5. `ai_analysis_results`에 새 레코드 저장 (`heatmap_url`은 1.2에 따라 원본 X-Ray URL 재사용)
6. 저장된 결과를 응답으로 반환

응답 예시:
```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 92.4,
  "heatmap_url": "/media/xray/xxx.png",
  "ai_model": "simple-cnn-v1",
  "created_at": "2026-08-31T10:00:00"
}
```

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 예측 성공 (신규 추론 또는 캐시된 결과 반환 모두 200) |
| `404 Not Found` | 존재하지 않는 진료기록, 또는 연결된 X-Ray 이미지가 없음 |

### 2.2 AI 예측 결과 목록 조회 — `REQ-PRED-002`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/medical-records/{record_id}/analyses` |
| 인증 | 필요 |

응답: 배열, 각 항목은 `id`, `is_pneumonia`, `confidence`, `heatmap_url`, `ai_model`, `created_at` 포함 (요구사항의 "고유 ID/폐렴여부/Confidence/Hitmap Image URL/예측 수행일시/사용한 모델" 6개 항목과 정확히 일치).

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 조회 성공 (결과 없으면 빈 배열) |
| `404 Not Found` | 존재하지 않는 진료기록 |

---

## 3. 공통 규칙

- 모든 API는 로그인 필요, PENDING 권한은 접근 불가 (기존 규칙과 동일)
- 3초 이내 응답 (`NFR-PRED-002`) — 다만 실제 추론 시간은 이미지 크기/CPU 성능에 따라 달라질 수 있어, 느리면 캐싱(2번 처리 순서)이 이 조건을 지키는 데 핵심적인 역할을 한다
- 모델 평가 기준(`NFR-PRED-001`, Recall ≥ 0.90 등)은 API 설계 대상이 아니라 **모델 자체의 품질 지표**다. 지금 쓰는 샘플 모델이 이 기준을 만족하는지는 별도로 검증된 바 없다 — 팀 AI 트랙의 실제 모델로 교체 시 이 기준으로 평가해야 한다.
