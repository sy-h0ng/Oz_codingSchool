# 4일차 User API 설계서

> 작성 기준: `4일차 - User 사용자 요구사항 정의서` (REQ-USER-001~009, NFR-USER-001~003) + 팀 `API 명세서 예시` 포맷
> AI(Claude) 활용하여 초안 작성 후 직접 검토·수정함

## 0. 공통 사항

| 항목 | 내용 |
| --- | --- |
| Base URL | `/api/v1` |
| 인증 방식 | JWT Bearer (Access Token), Refresh Token은 `httpOnly` 쿠키로 전달 |
| Access Token 만료 | 30분 (1800초) |
| Refresh Token 만료 | 7일 (604800초) |
| JWT payload | 최소 식별 정보인 `user_id`만 저장 |
| 토큰 재발급 | Access Token 만료 시 Refresh Token으로 재발급, Refresh Token까지 만료되면 재로그인 유도 |
| 비밀번호 입력 | 인풋 마스킹 처리, 보기 아이콘 클릭으로 확인 가능 |
| 응답 속도 | 모든 API는 3초 이내에 응답 |
| 권한(Role) | `pending`(대기자) / `staff`(스태프) / `admin`(어드민) |
| 권한별 접근 범위 | 대기자: 마이페이지 외 접근 불가 · 스태프: 흉부 X-ray 관련 데이터 읽기/쓰기/수정 가능 · 어드민: 시스템 관리 + 전체 데이터 접근 가능 |

## API 목록

| No | API 이름 | 메서드 | 엔드포인트 | 인증 필요 |
| --- | --- | --- | --- | --- |
| 1 | 회원가입 | POST | `/api/v1/users` | N |
| 2 | 로그인 | POST | `/api/v1/auth/login` | N |
| 3 | 로그아웃 | POST | `/api/v1/auth/logout` | Y |
| 4 | 회원 목록 조회 | GET | `/api/v1/users` | Y (Admin) |
| 5 | 회원 권한 변경 | PATCH | `/api/v1/users/{user_id}/role` | Y (Admin) |
| 6 | 마이페이지 조회 | GET | `/api/v1/users/me` | Y |
| 7 | 회원 정보 수정 | PATCH | `/api/v1/users/me` | Y |
| 8 | 비밀번호 변경 | PATCH | `/api/v1/users/me/password` | Y |
| 9 | 회원 탈퇴 | DELETE | `/api/v1/users/me` | Y |

---

## 1. 회원가입 API (REQ-USER-001)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원가입 API |
| 설명 | 사내 의료인, 개발 실무진이 회원가입을 통해 흉부 X-Ray AI 진단 서비스를 이용할 수 있도록 계정을 생성한다. |
| 엔드포인트(Endpoint) | `/api/v1/users` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 이메일 (로그인 ID) |
| password | string | Y | 비밀번호 |
| name | string | Y | 이름 |
| department | string | Y | 부서 (연구 / 의료 / 개발) |
| gender | string | Y | 성별 (M / F) |
| phone_number | string | Y | 휴대폰 번호 |

### 3) 응답(Response)

**성공**

- `201 Created`

```
{
  "id": 1,
  "email": "example@example.com",
  "name": "홍길동",
  "department": "의료",
  "gender": "F",
  "phone_number": "010-1234-5678",
  "role": "pending"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 사용자 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서 |
| gender | string | 성별 |
| phone_number | string | 휴대폰 번호 |
| role | string | 가입 직후 기본 권한(대기자) |

**실패**

- `409 Conflict`

```
{ "detail": "이미 가입된 이메일입니다." }
```

- `422 Unprocessable Entity` (필수 값 누락 또는 형식 오류) — 공통 형식은 0. 공통 사항 참고

### 4) 비고

- 가입 직후 기본 권한은 `pending`(대기자)이며, 이후 REQ-USER-005(회원 권한 변경)를 통해 Admin이 `staff`/`admin`으로 승급시킨다. (요구사항 정의서에 기본 권한이 명시되어 있지 않아 이렇게 가정 — 팀과 확인 필요)
- 비밀번호는 해시(bcrypt 등)로 저장하며 평문 저장하지 않는다.

---

## 2. 로그인 API (REQ-USER-002, NFR-USER-001)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그인 API |
| 설명 | 이메일과 비밀번호로 로그인하여 서비스 이용을 위한 JWT를 발급받는다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/login` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 이메일 |
| password | string | Y | 비밀번호 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "example@example.com",
    "name": "홍길동",
    "role": "staff"
  }
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| access_token | string | 30분 동안 유효한 JWT 액세스 토큰 |
| token_type | string | 토큰 인증 방식, bearer |
| expires_in | integer | 액세스 토큰 만료 시간(초), 1800 |
| user | object | 로그인한 사용자 정보 |
| user.id | integer | 사용자 ID |
| user.email | string | 사용자 이메일 |
| user.name | string | 사용자 이름 |
| user.role | string | 사용자 권한 |

**응답 Headers**

| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Set-Cookie | `refresh_token=<JWT>; HttpOnly; Secure; SameSite=Lax; Max-Age=604800` | 유효기간 7일의 JWT 리프레시 토큰 |

**실패**

- `401 Unauthorized`

```
{ "detail": "이메일 또는 비밀번호가 일치하지 않습니다." }
```

### 4) 비고

- JWT payload에는 최소 식별 정보인 `user_id`만 저장한다.
- 리프레시 토큰은 클라이언트 JS에서 접근할 수 없도록 `httpOnly` 쿠키로 전달한다.

---

## 3. 로그아웃 API (REQ-USER-003)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 로그아웃 API |
| 설명 | 로그인 유저가 상단 헤더의 로그아웃 버튼을 통해 로그아웃하고, 로그인 페이지로 전환된다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/logout` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | Y |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| - | - | - | 요청 본문을 사용하지 않음 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{ "detail": "로그아웃되었습니다." }
```

**응답 Headers**

| Key | 예시 값 | 설명 |
| --- | --- | --- |
| Set-Cookie | `refresh_token=; Max-Age=0` | 리프레시 토큰 쿠키 만료 처리 |

**실패**

- `401 Unauthorized`

```
{ "detail": "인증 정보가 유효하지 않습니다." }
```

### 4) 비고

- 액세스 토큰 자체는 만료 전까지 유효할 수 있으므로, 클라이언트는 로그아웃 시 저장된 access_token도 함께 폐기한다.

---

## 4. 회원 목록 조회 API (REQ-USER-004)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 목록 조회 API |
| 설명 | 관리자(Admin) 권한 유저가 회원관리 메뉴에서 전체 회원 목록을 조회한다. |
| 엔드포인트(Endpoint) | `/api/v1/users` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y (Admin) |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | Admin 권한 사용자 인증 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| search | string | N | 이메일 또는 이름으로 검색 |
| department | string | N | 부서(연구/의료/개발) 필터 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
[
  {
    "id": 1,
    "email": "example@example.com",
    "name": "홍길동",
    "department": "의료",
    "gender": "F",
    "phone_number": "010-1234-5678",
    "is_active": true
  }
]
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 사용자 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서 |
| gender | string | 성별 |
| phone_number | string | 휴대폰 번호 |
| is_active | boolean | 계정 활성화 여부 |

**실패**

- `403 Forbidden`

```
{ "detail": "관리자 권한이 필요합니다." }
```

### 4) 비고

- Admin 권한이 아닌 사용자가 요청할 경우 403을 반환한다.

---

## 5. 회원 권한 변경 API (REQ-USER-005)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 권한 변경 API |
| 설명 | 관리자(Admin) 권한 유저가 회원관리 메뉴에서 대상 회원을 선택하고 권한을 변경한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/{user_id}/role` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y (Admin) |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | Admin 권한 사용자 인증 |
| Content-Type | application/json | 요청 본문 형식 |

**경로 파라미터**

| 파라미터명 | 타입 | 설명 |
| --- | --- | --- |
| user_id | integer | 권한을 변경할 대상 회원 ID |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| role | string | Y | 변경할 권한 (`pending` / `staff` / `admin`) |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{
  "id": 5,
  "email": "example2@example.com",
  "name": "김철수",
  "role": "staff"
}
```

**실패**

- `403 Forbidden`

```
{ "detail": "관리자 권한이 필요합니다." }
```

- `404 Not Found`

```
{ "detail": "해당 회원을 찾을 수 없습니다." }
```

### 4) 비고

- 대기자: 마이페이지 외 모든 서비스 접근 불가
- 스태프: 내부 직원, 흉부 X-ray 관련 모든 읽기/쓰기/수정 작업 가능
- 어드민: 시스템 관리자, 모든 항목에 대한 데이터 액세스 가능

---

## 6. 마이페이지 조회 API (REQ-USER-006)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 마이페이지 조회 API |
| 설명 | 모든 로그인 유저가 마이페이지에서 본인의 정보를 확인한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| - | - | - | 요청 본문을 사용하지 않음 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{
  "id": 1,
  "name": "홍길동",
  "email": "example@example.com",
  "department": "의료",
  "gender": "F",
  "phone_number": "010-1234-5678",
  "role": "staff"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 사용자 ID |
| name | string | 이름 |
| email | string | 이메일 |
| department | string | 부서 |
| gender | string | 성별 |
| phone_number | string | 휴대폰 번호 |
| role | string | 권한 (대기자/스태프/어드민) |

**실패**

- `401 Unauthorized`

```
{ "detail": "인증 정보가 유효하지 않습니다." }
```

### 4) 비고

- 없음

---

## 7. 회원 정보 수정 API (REQ-USER-007)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원 정보 수정 API |
| 설명 | 모든 로그인 유저가 마이페이지에서 본인의 정보를 부분(Partial) 수정한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증 |
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| department | string | N | 부서 (연구/의료/개발) |
| phone_number | string | N | 휴대폰 번호 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{
  "id": 1,
  "name": "홍길동",
  "email": "example@example.com",
  "department": "개발",
  "gender": "F",
  "phone_number": "010-9999-8888",
  "role": "staff"
}
```

**실패**

- `422 Unprocessable Entity` (입력 형식 오류) — 공통 형식은 0. 공통 사항 참고

### 4) 비고

- 부서, 휴대폰번호 외 항목(이메일, 이름, 성별 등)은 이 API로 수정할 수 없다.

---

## 8. 비밀번호 변경 API (REQ-USER-008, NFR-USER-002)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 비밀번호 변경 API |
| 설명 | 모든 로그인 유저가 마이페이지에서 계정의 비밀번호를 변경한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me/password` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Authorization | Bearer {access_token} | 로그인 사용자 인증 |
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| current_password | string | Y | 기존 비밀번호 |
| new_password | string | Y | 새로운 비밀번호 |

### 3) 응답(Response)

**성공**

- `200 OK`

```
{ "detail": "비밀번호가 변경되었습니다." }
```

**실패**

- `401 Unauthorized`

```
{ "detail": "기존 비밀번호가 일치하지 않습니다." }
```

### 4) 비고

- 프론트엔드 비밀번호 입력창은 마스킹 처리하고, 보기 아이콘 클릭 시 입력값을 확인할 수 있도록 한다.
- 기존 비밀번호 일치 여부를 반드시 서버에서 재검증한 뒤 새 비밀번호를 적용한다.

---

## 9. 회원 탈퇴 API (REQ-USER-009)

### 1) API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 회원탈퇴 API |
| 설명 | 로그인한 사용자가 마이페이지에서 본인의 계정을 탈퇴한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `Delete` |
| 인증 필요 여부 | Y |

### 2) 요청(Request)

**Headers**

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 탈퇴할 현재 로그인 사용자 확인 |

**본문 필드**

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
| --- | --- | --- | --- |
| - | - | - | 요청 본문을 사용하지 않음 |

### 3) 응답(Response)

**성공**

- `204 No Content`

**실패**

- `401 Unauthorized`

```
{ "detail": "인증 정보가 유효하지 않습니다." }
```

### 4) 비고

- 회원탈퇴 시 Database에서 회원과 관련된 정보는 모두 즉시 삭제한다 (연관된 patients/medical_records 등 FK 관계 처리 방식은 구현 시 추가 확인 필요).
