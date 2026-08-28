# 5일차 환자관리 및 진료기록 API 설계

## 1. 개요

요구사항 정의서(REQ-PTNT-001~005, REQ-MDR-001~003, NFR)와 프론트엔드 코드(`static/apis.js`, `static/pages.js`, `static/templates/*.html`), 그리고 실제 `main`에 merge된 `app/models/patient.py`, `medical_record.py`, `xray_image.py`를 기준으로 설계했다.

### 1.1 중요: DB 필드명과 프론트엔드 필드명이 다르다

`app/models/patient.py`의 실제 컬럼명은 **`phone`**이다. 반면 프론트엔드(`apis.js`, `pages.js`, `patient-create.html` 등)는 요청/응답 어디서나 예외 없이 **`phone_number`**라는 키를 쓴다.

```python
# app/models/patient.py
phone: Mapped[str] = mapped_column(String(11), ...)
```
```js
// static/pages.js
phone_number: document.getElementById('phone_number').value...
```

즉 **API 스키마(Pydantic)에서는 `phone_number`라는 이름을 쓰고, 서비스/레포지토리 계층에서 DB의 `phone` 컬럼과 매핑**해줘야 한다. DB 컬럼명을 프론트엔드에 맞춰 바꾸지 않는다 (이미 마이그레이션이 merge되어 있어 재작업 비용이 큼).

### 1.2 X-Ray 이미지는 별도 테이블이다

`medical_records` 테이블 자체에는 이미지 필드가 없다. `xray_images` 테이블이 `medical_record_id`로 진료기록을 참조하는 구조다. 따라서 **진료기록 상세 조회 응답의 `xray_image_url`은, 연결된 `XrayImage`에서 값을 가져와 채워 넣어야 한다** (진료기록 등록 시 첨부된 X-Ray 1건을 기준으로 한다).

또한 `XrayImage.uploader_id`(업로드한 유저)는 **필수값**이다 — 진료기록 등록 API는 반드시 로그인된 유저(Day4에서 만든 `get_current_user`)의 id를 여기 넣어야 한다.

### 1.3 촬영일시(`shooting_datetime`) 처리

`XrayImage.shooting_datetime`은 DB상 필수 컬럼이지만, 요구사항 정의서와 실제 업로드 폼(`record-create.html`)에는 촬영일시를 입력받는 필드가 없다. **업로드 시점(서버 현재 시각)을 촬영일시로 대신 저장**한다.

### 1.4 이미지 저장 방식 (비고 반영)

이미지는 외부 스토리지가 아니라 **서버 로컬 파일시스템**에 저장한다. 프로젝트에 이미 `media/` 폴더가 `/media` 경로로 마운트되어 있으므로(`app/main.py`), 업로드된 파일을 `media/xray/` 하위에 저장하고 `image_url`에는 `/media/xray/{파일명}` 형태의 접근 경로를 저장한다.

---

## 2. 환자(Patient) API

### 2.1 환자 등록 — `REQ-PTNT-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/patients` |
| 인증 | 필요 (로그인 유저) |
| Request Body | `application/json` |

```json
{ "name": "김철수", "age": 45, "gender": "M", "phone_number": "01012345678" }
```

| 필드 | 규칙 |
| --- | --- |
| `name` | 필수, 최대 30자 |
| `age` | 필수, 정수 |
| `gender` | 필수, `M`/`F` |
| `phone_number` | 필수, 숫자만, 최대 11자 (DB `phone` 컬럼에 매핑) |

| 응답 | 설명 |
| --- | --- |
| `201 Created` | 등록된 환자 정보 반환 |
| `400 Bad Request` | 필드 형식 오류 |

### 2.2 환자 목록 조회 — `REQ-PTNT-002`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/patients` |
| 인증 | 필요 |
| Query Parameter | `name`(이름 검색, 부분일치), `gender`(성별 필터), `min_age`, `max_age`(나이 범위 필터) — 전부 선택 |

응답: 배열, 각 항목은 `id`, `name`, `age`, `gender`, `phone_number`, `created_at`, `updated_at` 포함.

### 2.3 환자 상세 조회 — `REQ-PTNT-003`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/patients/{patient_id}` |
| 인증 | 필요 |

응답: `name`, `gender`, `phone_number`, `age` (요구사항에 명시된 4개 항목. `id`는 경로에 이미 있으므로 응답에도 포함해 프론트에서 재사용하기 쉽게 한다).

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 조회 성공 |
| `404 Not Found` | 존재하지 않는 환자 |

### 2.4 환자 정보 수정 — `REQ-PTNT-004`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `PATCH /api/v1/patients/{patient_id}` |
| 인증 | 필요 |
| Request Body | `name`, `phone_number` (요구사항상 이 2개만 수정 가능, Partial) |

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 수정된 환자 정보 반환 |
| `404 Not Found` | 존재하지 않는 환자 |

### 2.5 환자 삭제 — `REQ-PTNT-005`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `DELETE /api/v1/patients/{patient_id}` |
| 인증 | 필요 |
| 동작 | 환자 삭제 시 연관된 진료기록·X-Ray 이미지도 함께 영구 삭제. DB에 이미 `ondelete="CASCADE"`로 설정되어 있어 환자만 지우면 자동으로 같이 삭제된다. |

| 응답 | 설명 |
| --- | --- |
| `204 No Content` | 삭제 성공 |
| `404 Not Found` | 존재하지 않는 환자 |

---

## 3. 진료기록(MedicalRecord) API

### 3.1 진료기록 등록 — `REQ-MDR-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/medical-records` |
| 인증 | 필요 |
| Request Body | `multipart/form-data` (`apis.js`가 FormData로 전송) |

| 필드 | 설명 |
| --- | --- |
| `patient_id` | 필수, 대상 환자 ID |
| `chart_number` | 필수, 최대 50자, 중복 불가 |
| `symptoms` | 필수 |
| `xray_image` | 필수, 이미지 파일 |

처리 순서: 환자 존재 확인 → `medical_records` 생성 → 업로드된 파일을 `media/xray/`에 저장 → `xray_images`에 `record_id`, `uploader_id`(현재 로그인 유저), `image_url`, `shooting_datetime`(현재 시각)으로 저장.

| 응답 | 설명 |
| --- | --- |
| `201 Created` | 등록된 진료기록 정보 반환 |
| `404 Not Found` | 존재하지 않는 환자 |
| `409 Conflict` | 차트 번호 중복 |

### 3.2 환자별 진료기록 목록 조회 — `REQ-MDR-002`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/patients/{patient_id}/medical-records` |
| 인증 | 필요 |

응답: 배열, 각 항목은 `id`, `chart_number`, `symptoms`(100자 초과 시 97자 + `...`로 잘라서 반환), `created_at` 포함. **자르는 처리는 서버(API)에서 한다** — 프론트엔드 코드(`pages.js`)에 별도 축약 로직이 없기 때문이다.

### 3.3 진료기록 상세 조회 — `REQ-MDR-003`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/medical-records/{record_id}` |
| 인증 | 필요 |

응답: `id`, `chart_number`, `symptoms`(전체, 축약 없음), `xray_image_url`(연결된 `XrayImage.image_url`), `created_at`, `patient_id`(뒤로가기 버튼이 `record.patient_id`를 사용하므로 포함).

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 조회 성공 |
| `404 Not Found` | 존재하지 않는 진료기록 |

---

## 4. 공통 규칙

- 모든 API는 로그인 필요 (Day4에서 만든 `get_current_user` 재사용)
- 모든 응답은 3초 이내 처리 (`NFR-PTNT-001`, `NFR-MDR-001`)
- `phone_number` ↔ DB `phone` 매핑은 서비스/레포지토리 계층에서 처리, 스키마 바깥(API 응답)으로는 항상 `phone_number`로 노출
