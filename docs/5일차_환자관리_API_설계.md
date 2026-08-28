# 5일차 환자관리 API 설계

## 1. 문서 목적

이 문서는 5일차 진료기록 사용자 요구사항 정의서를 기준으로, AI Health 프로젝트의 환자 관리 및 진료기록 API를 설계한 문서이다.

설계 기준은 다음과 같다.

- GitHub `main` 브랜치에 있는 최신 프로젝트 구조
- 기존 프론트엔드 코드 `static/apis.js`, `static/pages.js`
- 기존 DB 모델 `patients`, `medical_records`, `xray_images`
- 요구사항 `REQ-PTNT-001~005`, `REQ-MDR-001~003`, `NFR-PTNT-001`, `NFR-MDR-001`

## 2. 공통 API 기준

### Base URL

```text
/api/v1
```

예시:

```text
GET /api/v1/patients
```

### 인증 방식

로그인 후 발급받은 Access Token을 Authorization 헤더에 담아 요청한다.

```http
Authorization: Bearer {access_token}
```

### 공통 응답 시간

모든 환자 관리 API와 진료기록 API는 최대 3초 이내에 로직을 처리하고 응답한다.

### 권한 기준

| 권한 | 접근 범위 |
| --- | --- |
| `PENDING` | 마이페이지 외 서비스 접근 불가 |
| `STAFF` | 환자 및 진료기록 등록, 조회, 수정 가능 |
| `ADMIN` | 모든 환자 및 진료기록 데이터 접근 가능 |

요구사항 이미지에는 "로그인 된 사내 개발진, 의료 실무진, 연구진" 또는 "사내 의료인 역할을 가진 유저"라는 표현이 함께 있다. 이 문서에서는 기존 User API 설계의 권한 체계를 따라 `STAFF`, `ADMIN` 사용자가 환자/진료기록 기능을 사용할 수 있도록 설계한다.

### 공통 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 로그인하지 않았거나 토큰이 올바르지 않은 경우 |
| `403 Forbidden` | 권한이 부족한 경우 |
| `404 Not Found` | 환자 또는 진료기록을 찾을 수 없는 경우 |
| `422 Unprocessable Entity` | 요청값 형식이 올바르지 않은 경우 |

## 3. Enum 정의

### 성별

기존 프론트엔드 `patient-create.html`, `patients.html` 기준으로 환자 성별 값은 다음과 같이 사용한다.

| 값 | 설명 |
| --- | --- |
| `male` | 남성 |
| `female` | 여성 |

단, 기존 DB 모델의 `GenderEnum` 값이 `M`, `F`인 경우 백엔드 구현 시 프론트엔드 값과 DB 저장값 사이의 변환 처리가 필요하다.

## 4. API 목록

| 요구사항 ID | 기능 | Method | Endpoint | 인증 | 권한 |
| --- | --- | --- | --- | --- | --- |
| REQ-PTNT-001 | 환자 정보 등록 | `POST` | `/patients` | 필요 | `STAFF`, `ADMIN` |
| REQ-PTNT-002 | 환자 목록 조회 | `GET` | `/patients` | 필요 | `STAFF`, `ADMIN` |
| REQ-PTNT-003 | 환자 정보 상세 조회 | `GET` | `/patients/{patient_id}` | 필요 | `STAFF`, `ADMIN` |
| REQ-PTNT-004 | 환자 정보 수정 | `PATCH` | `/patients/{patient_id}` | 필요 | `STAFF`, `ADMIN` |
| REQ-PTNT-005 | 환자 정보 삭제 | `DELETE` | `/patients/{patient_id}` | 필요 | `STAFF`, `ADMIN` |
| REQ-MDR-001 | 진료기록 등록 | `POST` | `/medical-records` | 필요 | `STAFF`, `ADMIN` |
| REQ-MDR-002 | 환자별 진료기록 목록 조회 | `GET` | `/patients/{patient_id}/medical-records` | 필요 | `STAFF`, `ADMIN` |
| REQ-MDR-003 | 진료기록 상세 조회 | `GET` | `/medical-records/{record_id}` | 필요 | `STAFF`, `ADMIN` |
| 추가 설계 | 진료기록 수정 | `PATCH` | `/medical-records/{record_id}` | 필요 | `STAFF`, `ADMIN` |
| 추가 설계 | 진료기록 삭제 | `DELETE` | `/medical-records/{record_id}` | 필요 | `STAFF`, `ADMIN` |

## 5. API 상세 명세

### 5.1 환자 정보 등록

사내 의료인 역할을 가진 사용자는 환자 관리 메뉴에서 환자 정보를 등록할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PTNT-001 |
| Method | `POST` |
| Endpoint | `/patients` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Request Body

```json
{
  "name": "김환자",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678"
}
```

#### Request Field

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `name` | string | 예 | 환자 이름 |
| `age` | integer | 예 | 환자 나이 |
| `gender` | string | 예 | `male`, `female` |
| `phone_number` | string | 예 | 환자 연락처 |

#### Response `201 Created`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678",
  "created_at": "2026-08-28T10:00:00",
  "updated_at": null
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `403 Forbidden` | 환자 등록 권한이 없는 경우 |
| `422 Unprocessable Entity` | 필수값이 누락되었거나 형식이 맞지 않는 경우 |

### 5.2 환자 목록 조회

로그인 된 사내 개발진, 의료 실무진, 연구진은 환자 관리 메뉴에서 의료진이 등록한 환자 정보를 목록으로 조회할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PTNT-002 |
| Method | `GET` |
| Endpoint | `/patients` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Query Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `name` | string | 아니오 | 환자 이름 검색 |
| `gender` | string | 아니오 | `male`, `female` 기준 필터 |
| `min_age` | integer | 아니오 | 최소 나이 |
| `max_age` | integer | 아니오 | 최대 나이 |

#### Request Example

```text
GET /api/v1/patients?name=김&gender=male&min_age=20&max_age=80
```

#### Response `200 OK`

```json
[
  {
    "id": 1,
    "name": "김환자",
    "age": 45,
    "gender": "male",
    "phone_number": "01012345678",
    "created_at": "2026-08-28T10:00:00",
    "updated_at": null
  }
]
```

#### 조회 가능한 필드

| 필드 | 설명 |
| --- | --- |
| `id` | 환자 고유 ID |
| `name` | 환자 이름 |
| `age` | 환자 나이 |
| `gender` | 환자 성별 |
| `phone_number` | 환자 연락처 |
| `created_at` | 생성일시 |
| `updated_at` | 수정일시 |

### 5.3 환자 정보 상세 조회

환자 관리 메뉴에서 특정 환자의 상세보기 버튼을 클릭하면 환자 상세 정보 페이지로 이동하여 환자 정보를 확인할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PTNT-003 |
| Method | `GET` |
| Endpoint | `/patients/{patient_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `patient_id` | integer | 예 | 조회할 환자 ID |

#### Response `200 OK`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678",
  "created_at": "2026-08-28T10:00:00",
  "updated_at": null
}
```

#### 확인 가능한 필드

| 필드 | 설명 |
| --- | --- |
| `name` | 환자 이름 |
| `gender` | 환자 성별 |
| `phone_number` | 환자 연락처 |
| `age` | 환자 나이 |

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 환자가 존재하지 않는 경우 |

### 5.4 환자 정보 수정

환자 정보 상세보기 페이지에서 정보 수정 버튼을 클릭하여 환자의 정보를 수정할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PTNT-004 |
| Method | `PATCH` |
| Endpoint | `/patients/{patient_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Request Body

기존 프론트엔드 수정 모달은 이름과 연락처만 수정하도록 되어 있다.

```json
{
  "name": "김수정",
  "phone_number": "01099998888"
}
```

#### Request Field

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `name` | string | 아니오 | 수정할 환자 이름 |
| `phone_number` | string | 아니오 | 수정할 환자 연락처 |

#### Response `200 OK`

```json
{
  "id": 1,
  "name": "김수정",
  "age": 45,
  "gender": "male",
  "phone_number": "01099998888",
  "created_at": "2026-08-28T10:00:00",
  "updated_at": "2026-08-28T10:20:00"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `400 Bad Request` | 수정할 항목을 하나도 입력하지 않은 경우 |
| `404 Not Found` | 해당 환자가 존재하지 않는 경우 |

### 5.5 환자 정보 삭제

환자 정보 상세보기 페이지에서 삭제 버튼을 클릭하면 확인 모달이 표시되고, 확인했습니다 버튼 클릭 시 환자와 관련된 진료기록 및 X-Ray 이미지가 함께 영구 삭제된다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PTNT-005 |
| Method | `DELETE` |
| Endpoint | `/patients/{patient_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Response `204 No Content`

응답 본문 없음.

#### 삭제 범위

| 대상 | 설명 |
| --- | --- |
| `patients` | 환자 기본 정보 |
| `medical_records` | 해당 환자의 모든 진료기록 |
| `xray_images` | 해당 환자 진료기록에 연결된 X-Ray 이미지 |
| `ai_analysis_results` | 해당 환자 진료기록에 연결된 AI 분석 결과 |

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 환자가 존재하지 않는 경우 |

### 5.6 진료기록 등록

사내 의료인 역할을 가진 사용자는 환자 상세 정보 페이지의 진료 기록 목록 섹션에서 진료 기록 등록 버튼을 클릭하여 진료기록을 등록할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-MDR-001 |
| Method | `POST` |
| Endpoint | `/medical-records` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |
| Content-Type | `multipart/form-data` |

#### Request Form Data

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `patient_id` | integer | 예 | 환자 고유 ID |
| `chart_number` | string | 예 | 진료 차트 번호 |
| `symptoms` | string | 예 | 진료된 증상 |
| `xray_image` | file | 예 | 촬영된 흉부 X-Ray 이미지 |

#### Request Example

```text
patient_id=1
chart_number=CHART-20260828-001
symptoms=기침과 발열 증상
xray_image=chest_xray.png
```

이미지 업로드 시 프론트엔드에서 업로드된 이미지 미리보기를 제공한다. 서버는 이미지 파일을 실행 환경의 로컬 저장소에 저장하고, DB에는 접근 가능한 이미지 경로를 저장한다.

#### Response `201 Created`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "CHART-20260828-001",
  "symptoms": "기침과 발열 증상",
  "xray_image_url": "/media/xrays/chest_xray.png",
  "created_at": "2026-08-28T10:30:00"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 환자가 존재하지 않는 경우 |
| `409 Conflict` | 이미 사용 중인 차트 번호인 경우 |
| `422 Unprocessable Entity` | 필수값 또는 이미지 파일이 누락된 경우 |

### 5.7 환자별 진료기록 목록 조회

환자 상세 정보 페이지의 진료 기록 목록 섹션에서 해당 환자의 진료기록을 목록으로 확인할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-MDR-002 |
| Method | `GET` |
| Endpoint | `/patients/{patient_id}/medical-records` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `patient_id` | integer | 예 | 진료기록을 조회할 환자 ID |

#### Response `200 OK`

```json
[
  {
    "id": 1,
    "chart_number": "CHART-20260828-001",
    "symptoms": "기침과 발열 증상",
    "created_at": "2026-08-28T10:30:00"
  }
]
```

#### 조회 가능한 필드

| 필드 | 설명 |
| --- | --- |
| `id` | 진료 기록 ID |
| `chart_number` | 진료 차트 번호 |
| `symptoms` | 증상, 100자 초과 시 말줄임 가능 |
| `created_at` | 생성일시 |

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 환자가 존재하지 않는 경우 |

### 5.8 진료기록 상세 조회

환자 상세 정보 페이지에서 진료기록 항목의 상세보기 버튼을 클릭하면 진료기록 상세 페이지로 이동하여 상세 내용을 확인할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-MDR-003 |
| Method | `GET` |
| Endpoint | `/medical-records/{record_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `record_id` | integer | 예 | 조회할 진료기록 ID |

#### Response `200 OK`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "CHART-20260828-001",
  "symptoms": "기침과 발열 증상",
  "xray_image_url": "/media/xrays/chest_xray.png",
  "created_at": "2026-08-28T10:30:00"
}
```

#### 상세 조회 가능한 필드

| 필드 | 설명 |
| --- | --- |
| `id` | 진료 기록 ID |
| `patient_id` | 연결된 환자 ID |
| `chart_number` | 차트 번호 |
| `symptoms` | 증상 |
| `xray_image_url` | 흉부 X-Ray 이미지 경로 |
| `created_at` | 생성일시 |

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 진료기록이 존재하지 않는 경우 |

### 5.9 진료기록 수정

요구사항은 진료기록의 등록, 조회, 수정, 삭제 API 설계를 요구하므로 진료기록 수정 API를 함께 설계한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 | 진료기록 수정 |
| Method | `PATCH` |
| Endpoint | `/medical-records/{record_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |
| Content-Type | `multipart/form-data` |

#### Request Form Data

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `chart_number` | string | 아니오 | 수정할 진료 차트 번호 |
| `symptoms` | string | 아니오 | 수정할 증상 |
| `xray_image` | file | 아니오 | 새로 교체할 X-Ray 이미지 |

#### Response `200 OK`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "CHART-20260828-002",
  "symptoms": "기침 증상 완화",
  "xray_image_url": "/media/xrays/chest_xray_updated.png",
  "created_at": "2026-08-28T10:30:00",
  "updated_at": "2026-08-28T11:00:00"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `400 Bad Request` | 수정할 항목을 하나도 입력하지 않은 경우 |
| `404 Not Found` | 해당 진료기록이 존재하지 않는 경우 |
| `409 Conflict` | 이미 사용 중인 차트 번호로 수정하려는 경우 |

### 5.10 진료기록 삭제

요구사항은 진료기록의 등록, 조회, 수정, 삭제 API 설계를 요구하므로 진료기록 삭제 API를 함께 설계한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 | 진료기록 삭제 |
| Method | `DELETE` |
| Endpoint | `/medical-records/{record_id}` |
| 인증 | 필요 |
| 권한 | `STAFF`, `ADMIN` |

#### Response `204 No Content`

응답 본문 없음.

#### 삭제 범위

| 대상 | 설명 |
| --- | --- |
| `medical_records` | 진료기록 기본 정보 |
| `xray_images` | 해당 진료기록에 연결된 X-Ray 이미지 |
| `ai_analysis_results` | 해당 진료기록에 연결된 AI 분석 결과 |

#### Error

| Status | 상황 |
| --- | --- |
| `404 Not Found` | 해당 진료기록이 존재하지 않는 경우 |

## 6. API 구현 흐름

### 환자 관리 흐름

```text
프론트엔드 화면
→ static/apis.js의 환자 API 함수 호출
→ FastAPI Router
→ Service에서 권한/입력값 검증
→ Repository에서 DB 조회 또는 저장
→ patients 테이블 반영
→ JSON 응답 반환
```

### 진료기록 등록 흐름

```text
진료기록 등록 화면
→ chart_number, symptoms, xray_image 입력
→ multipart/form-data로 /api/v1/medical-records 요청
→ 서버가 patient_id 존재 여부 확인
→ 이미지 파일을 로컬 저장소에 저장
→ medical_records 테이블에 진료기록 저장
→ xray_images 테이블에 이미지 경로 저장
→ 생성된 진료기록 정보 반환
```

## 7. 프론트엔드 연동 기준

기존 프론트엔드에서 이미 호출하고 있는 API 함수와 맞춰 설계했다.

| 프론트엔드 함수 | 호출 API |
| --- | --- |
| `apis.createPatient(patientData)` | `POST /api/v1/patients` |
| `apis.getPatients(params)` | `GET /api/v1/patients` |
| `apis.getPatient(patientId)` | `GET /api/v1/patients/{patient_id}` |
| `apis.updatePatient(patientId, patientData)` | `PATCH /api/v1/patients/{patient_id}` |
| `apis.deletePatient(patientId)` | `DELETE /api/v1/patients/{patient_id}` |
| `apis.createMedicalRecord(formData)` | `POST /api/v1/medical-records` |
| `apis.getPatientMedicalRecords(patientId)` | `GET /api/v1/patients/{patient_id}/medical-records` |
| `apis.getMedicalRecord(recordId)` | `GET /api/v1/medical-records/{record_id}` |

진료기록 수정/삭제는 요구사항의 CRUD 설계 범위를 맞추기 위해 추가 설계했으며, 현재 프론트엔드에 버튼이 없다면 추후 화면에서 같은 endpoint를 호출하도록 연결하면 된다.
