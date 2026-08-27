# User API 명세서

> AI 헬스케어 캠프 - 4일차 User 사용자 요구사항 정의서 기반 API 명세서

## 목차

1. [회원가입](#1-회원가입)
2. [로그인](#2-로그인)
3. [로그아웃](#3-로그아웃)
4. [회원 목록 조회](#4-회원-목록-조회)
5. [회원 권한 변경](#5-회원-권한-변경)
6. [마이페이지 조회](#6-마이페이지-조회)
7. [회원 정보 수정](#7-회원-정보-수정)
8. [비밀번호 변경](#8-비밀번호-변경)
9. [회원 탈퇴](#9-회원-탈퇴)

---

## 1. 회원가입

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원가입 API |
| 설명 | 사내 의료인, 개발 실무진이 흉부 X-Ray AI 진단 서비스를 이용하기 위해 회원가입을 진행한다. |
| 엔드포인트(Endpoint) | `/api/v1/users` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Content-Type | `application/json` | 요청 본문 타입 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| email | string | Y | 사용자 이메일 |
| password | string | Y | 비밀번호 |
| name | string | Y | 사용자 이름 |
| department | string | Y | 부서 (연구 / 의료 / 개발) |
| gender | string | Y | 성별 (M / F) |
| phone | string | Y | 휴대폰 번호 |

### 3. 응답(Response)

#### 성공

- `201 Created`

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "홍길동",
  "department": "의료",
  "gender": "M",
  "phone": "010-0000-0000",
  "role": "대기자"
}
```

#### 실패

- `400 Bad Request`

```json
{
  "detail": "이미 가입된 이메일입니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 이메일 중복 등 유효성 오류 메시지 |

---

## 2. 로그인

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 로그인 API |
| 설명 | 회원가입을 한 사용자가 이메일과 비밀번호를 입력하여 로그인을 진행한다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/login` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Content-Type | `application/json` | 요청 본문 타입 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| email | string | Y | 사용자 이메일 |
| password | string | Y | 비밀번호 |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
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
|---|---|---|
| access_token | string | 엑세스 토큰 (JWT) |
| token_type | string | 토큰 타입 |
| expires_in | int | 엑세스 토큰 만료 시간(초) |
| user.id | int | 사용자 ID |
| user.email | string | 사용자 이메일 |
| user.name | string | 사용자 이름 |
| user.role | string | 사용자 권한 |

#### 응답 Headers

| Key | 예시 값 | 설명 |
|---|---|---|
| Set-Cookie | `refresh_token=<JWT>; HttpOnly; Secure; SameSite=Lax; Max-Age=604800` | 유효기간 7일의 JWT 리프레시 토큰 |

#### 실패

- `401 Unauthorized`

```json
{
  "detail": "이메일 또는 비밀번호가 일치하지 않습니다."
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| detail | string | 이메일 또는 비밀번호가 올바르지 않은 경우의 오류 메시지 |

---

## 3. 로그아웃

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 로그아웃 API |
| 설명 | 로그인한 사용자가 헤더의 로그아웃 버튼을 통해 로그아웃을 진행하며, 로그아웃 시 로그인 페이지로 전환된다. |
| 엔드포인트(Endpoint) | `/api/v1/auth/logout` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | Y |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 인증된 사용자 확인 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| - | - | - | 요청 본문을 사용하지 않음 |

### 3. 응답(Response)

#### 성공

- `204 No Content`

#### 실패

- `401 Unauthorized`

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

---

## 4. 회원 목록 조회

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원 목록 조회 API |
| 설명 | 관리자 권한(Admin) 사용자가 회원관리 메뉴에서 모든 회원을 목록으로 조회한다. |
| 엔드포인트(Endpoint) | `/api/v1/users` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y (Admin) |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 관리자 권한 확인 |

#### 쿼리 파라미터 (GET 요청 시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| keyword | string | N | 이메일 또는 이름으로 검색 |
| department | string | N | 부서별 필터 (연구 / 의료 / 개발) |
| page | int | N | 페이지 번호 |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
{
  "total": 1,
  "items": [
    {
      "id": 1,
      "email": "example@example.com",
      "name": "홍길동",
      "department": "의료",
      "gender": "M",
      "phone": "010-0000-0000",
      "is_active": true
    }
  ]
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | int | 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서(연구, 의료, 개발) |
| gender | string | 성별(M / F) |
| phone | string | 휴대폰 번호 |
| is_active | boolean | 계정 활성화 여부 |

#### 실패

- `403 Forbidden`

```json
{
  "detail": "관리자만 접근할 수 있습니다."
}
```

---

## 5. 회원 권한 변경

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원 권한 변경 API |
| 설명 | 관리자 권한(Admin) 사용자가 회원관리 메뉴에서 선택된 회원의 권한을 변경한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/{user_id}/role` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y (Admin) |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 관리자 권한 확인 |
| Content-Type | `application/json` | 요청 본문 타입 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| role | string | Y | 변경할 권한 (대기자 / 스태프 / 어드민) |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
{
  "id": 5,
  "role": "스태프"
}
```

#### 실패

- `403 Forbidden`

```json
{
  "detail": "관리자만 접근할 수 있습니다."
}
```

- `404 Not Found`

```json
{
  "detail": "해당 회원을 찾을 수 없습니다."
}
```

---

## 6. 마이페이지 조회

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 마이페이지 조회 API |
| 설명 | 로그인한 사용자가 마이페이지에서 본인의 정보를 확인한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `GET` |
| 인증 필요 여부 | Y |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 사용자 확인 |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
{
  "id": 1,
  "name": "홍길동",
  "email": "example@example.com",
  "department": "의료",
  "gender": "M",
  "phone": "010-0000-0000",
  "role": "스태프"
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| name | string | 이름 |
| email | string | 이메일 |
| department | string | 부서(연구, 의료, 개발) |
| gender | string | 성별(M / F) |
| phone | string | 휴대폰 번호 |
| role | string | 권한(대기자, 스태프, 어드민) |

#### 실패

- `401 Unauthorized`

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

---

## 7. 회원 정보 수정

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원 정보 수정 API |
| 설명 | 로그인한 사용자가 마이페이지에서 본인의 정보를 부분(Partial) 수정한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 사용자 확인 |
| Content-Type | `application/json` | 요청 본문 타입 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| department | string | N | 수정할 부서 |
| phone | string | N | 수정할 휴대폰 번호 |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
{
  "id": 1,
  "department": "개발",
  "phone": "010-1234-5678"
}
```

#### 실패

- `422 Unprocessable Entity`

```json
{
  "detail": "휴대폰 번호 형식이 올바르지 않습니다."
}
```

---

## 8. 비밀번호 변경

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 비밀번호 변경 API |
| 설명 | 로그인한 사용자가 마이페이지에서 계정의 비밀번호를 변경한다. 기존 비밀번호 일치 여부를 검증한 후 새로운 비밀번호를 적용한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me/password` |
| 메서드(Method) | `PATCH` |
| 인증 필요 여부 | Y |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 사용자 확인 |
| Content-Type | `application/json` | 요청 본문 타입 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| current_password | string | Y | 기존 비밀번호 |
| new_password | string | Y | 새로운 비밀번호 |

### 3. 응답(Response)

#### 성공

- `200 OK`

```json
{
  "detail": "비밀번호가 성공적으로 변경되었습니다."
}
```

#### 실패

- `400 Bad Request`

```json
{
  "detail": "기존 비밀번호가 일치하지 않습니다."
}
```

---

## 9. 회원 탈퇴

### 1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원탈퇴 API |
| 설명 | 로그인한 사용자가 마이페이지에서 본인의 계정을 탈퇴한다. |
| 엔드포인트(Endpoint) | `/api/v1/users/me` |
| 메서드(Method) | `DELETE` |
| 인증 필요 여부 | Y |

### 2. 요청(Request)

#### Headers

| Key | Value | 설명 |
|---|---|---|
| Content-Type | `application/json` | 탈퇴할 현재 로그인 사용자 확인 |

#### 본문 필드

| 파라미터명 | 타입 | 필수(Y/N) | 설명 |
|---|---|---|---|
| - | - | - | 요청 본문을 사용하지 않음 |

#### 쿼리 파라미터 (GET 요청 시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | N | 로그인 API는 쿼리 파라미터를 사용하지 않음 |

### 3. 응답(Response)

#### 성공

- `204 No Content`

> 회원탈퇴 시 Database에서 회원과 관련된 정보는 모두 즉시 삭제된다.

#### 실패

- `401 Unauthorized`

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```
