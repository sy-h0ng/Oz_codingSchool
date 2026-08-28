# 4일차 User API 설계

## 1. 개요

요구사항 정의서(REQ-USER-001~009, NFR-USER-001~003)와 프론트엔드 코드(`static/apis.js`, `static/pages.js`)를 기준으로 설계했다. 실제 `main`에 merge된 `app/models/user.py`, `app/models/enums.py`의 필드/Enum과 정확히 일치시켰다.

### 1.1 권한(Role) 정책

| Role | 의미 | 접근 범위 |
| --- | --- | --- |
| `PENDING` | 승인 대기 | 마이페이지 외 모든 서비스 접근 불가 |
| `STAFF` | 일반 직원 | 흉부 X-Ray 관련 모든 읽기/쓰기/수정 가능 |
| `ADMIN` | 관리자 | 모든 데이터 접근 가능, 회원관리 가능 |

가입 직후 기본 role은 `PENDING`이며, `ADMIN`이 `REQ-USER-005` API로 승인(권한 변경)해야 서비스를 이용할 수 있다.

### 1.2 인증 방식 (NFR-USER-001)

- 로그인 성공 시 **Access Token**(JWT, 응답 body에 JSON으로 반환)과 **Refresh Token**(JWT, `httpOnly` 쿠키로 전달)을 함께 발급한다.
- Access Token 만료: **30분** / Refresh Token 만료: **7일**
- JWT payload에는 `user_id`만 담는다 (그 외 개인정보 포함 금지).
- Access Token 만료 시 `POST /users/refresh`로 재발급받는다. Refresh Token까지 만료되면 재로그인이 필요하다 (`static/apis.js`의 401 처리 로직과 일치).
- 이후 모든 인증 필요 API는 `Authorization: Bearer <access_token>` 헤더로 요청한다.

---

## 2. 엔드포인트 명세

### 2.1 회원가입 — `REQ-USER-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/users/signup` |
| 인증 | 불필요 |
| Request Body | `application/json` |

```json
{
  "email": "gildong@ozcoding.com",
  "password": "Passw0rd!!",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678"
}
```

| 필드 | 규칙 |
| --- | --- |
| `email` | 이메일 형식(정규식 검증), 최대 255자, 중복 불가 |
| `password` | 최소 8자, 대문자·소문자·숫자·특수문자 각 1개 이상 포함 |
| `name` | 최대 20자, 필수 |
| `department` | `MEDICAL` / `DEV` / `RESEARCH` 중 하나 |
| `gender` | `M` / `F` 중 하나 |
| `phone_number` | 숫자만, 최대 20자, 중복 불가 |

가입 시 `role`은 서버에서 강제로 `PENDING`, `is_active`는 `true`로 저장한다 (요청 body로 role을 받지 않는다 — 클라이언트가 임의로 관리자 권한을 요청하는 것을 막기 위함).

| 응답 | 설명 |
| --- | --- |
| `201 Created` | 가입 성공, 생성된 유저 정보(비밀번호 제외) 반환 |
| `400 Bad Request` | 비밀번호/이메일 형식 오류 |
| `409 Conflict` | 이메일 또는 휴대폰 번호 중복 |

---

### 2.2 로그인 — `REQ-USER-002`, `NFR-USER-001`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/users/login` |
| 인증 | 불필요 |
| Request Body | `application/x-www-form-urlencoded` (OAuth2 password flow — `username`에 이메일 입력, `static/apis.js` 참고) |

응답:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```
동시에 `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax`로 리프레시 토큰 전달.

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 로그인 성공 |
| `401 Unauthorized` | 이메일 또는 비밀번호 불일치 |

---

### 2.3 토큰 재발급

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/users/refresh` |
| 인증 | Refresh Token(쿠키) 필요 |
| Request Body | 없음 (쿠키에서 자동으로 읽음) |

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 새 Access Token 발급 (body로 반환) |
| `401 Unauthorized` | Refresh Token 만료/없음 → 프론트에서 로그인 페이지로 이동 |

---

### 2.4 로그아웃 — `REQ-USER-003`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `POST /api/v1/users/logout` |
| 인증 | 필요 (Access Token) |
| 동작 | Refresh Token 쿠키 만료 처리(삭제) |
| 응답 | `204 No Content` |

---

### 2.5 마이페이지 조회 — `REQ-USER-006`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/users/me` |
| 인증 | 필요 (모든 로그인 유저, role 무관) |

응답 예시:
```json
{
  "id": 1,
  "email": "gildong@ozcoding.com",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "STAFF"
}
```
(`hashed_password`는 절대 응답에 포함하지 않는다.)

---

### 2.6 회원 정보 수정 — `REQ-USER-007`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `PATCH /api/v1/users/me` |
| 인증 | 필요 |
| Request Body | `department`, `phone_number` (둘 다 선택 입력, Partial Update) |

```json
{ "department": "DEV", "phone_number": "01099998888" }
```

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 수정된 유저 정보 반환 |
| `400 Bad Request` | 아무 필드도 입력하지 않은 경우 |

---

### 2.7 비밀번호 변경 — `REQ-USER-008`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `PATCH /api/v1/users/me/password` |
| 인증 | 필요 |
| Request Body | `current_password`, `new_password` (둘 다 필수) |

처리 순서: `current_password`가 저장된 해시와 일치하는지 검증 → 일치하면 `new_password`를 해싱해서 저장.

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 변경 성공 |
| `400 Bad Request` | `current_password` 불일치, 또는 `new_password` 형식 위반 |

---

### 2.8 회원 탈퇴 — `REQ-USER-009`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `DELETE /api/v1/users/me` |
| 인증 | 필요 |
| 동작 | 본인 계정 및 연관 데이터를 DB에서 **즉시 완전 삭제**(hard delete, soft delete 아님) |
| 응답 | `204 No Content` |

---

### 2.9 회원 목록 조회 (관리자) — `REQ-USER-004`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `GET /api/v1/admin/users` |
| 인증 | 필요, **`role=ADMIN`만 허용** |
| Query Parameter | `query`(이메일/이름 검색, 선택), `department`(부서 필터, 선택) |

응답: 배열, 각 항목은 `id`, `email`, `name`, `department`, `gender`, `phone_number`, `is_active` 포함 (role은 목록에서 노출 안 함 — 상세/수정 API에서 다룸, 필요 시 조정 가능).

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 조회 성공 (결과 없으면 빈 배열) |
| `403 Forbidden` | `ADMIN`이 아닌 유저가 요청 |

---

### 2.10 회원 권한 변경 (관리자) — `REQ-USER-005`

| 항목 | 내용 |
| --- | --- |
| Method / URL | `PATCH /api/v1/admin/users/role` |
| 인증 | 필요, **`role=ADMIN`만 허용** |
| Request Body | `user_id`, `new_role`(`PENDING`/`STAFF`/`ADMIN`) |

```json
{ "user_id": 3, "new_role": "STAFF" }
```

| 응답 | 설명 |
| --- | --- |
| `200 OK` | 변경된 유저 정보 반환 |
| `400 Bad Request` | `new_role`이 허용된 값이 아님 |
| `403 Forbidden` | `ADMIN`이 아닌 유저가 요청, 또는 본인 권한을 스스로 변경하려는 경우 |
| `404 Not Found` | 존재하지 않는 `user_id` |

---

## 3. 공통 규칙

- 모든 응답은 3초 이내 처리 (`NFR-USER-003`)
- 인증 필요 API에 토큰 없이 접근 시 `401 Unauthorized`
- `PENDING` 권한 유저가 마이페이지(2.5~2.8) 외 API에 접근 시 `403 Forbidden`
- 비밀번호는 응답 어디에도 평문/해시 형태로 노출하지 않는다
