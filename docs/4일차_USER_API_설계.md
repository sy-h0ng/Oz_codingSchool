# 4일차 USER API 설계

## 1. 문서 목적

이 문서는 4일차 사용자 요구사항 정의서를 바탕으로 AI Health 프로젝트의 User API를 설계한 문서이다.

User API는 사내 의료인, 개발 실무진, 연구진이 흉부 X-Ray AI 진단 서비스를 안전하게 사용할 수 있도록 회원가입, 로그인, 인증/인가, 마이페이지, 관리자 회원 관리 기능을 제공한다.

## 2. 공통 API 기준

### Base URL

```text
/api/v1
```

예시:

```text
POST /api/v1/users/signup
```

### 인증 방식

로그인 성공 시 JWT를 발급한다.

| 토큰 | 전달 방식 | 만료 시간 | 용도 |
| --- | --- | --- | --- |
| Access Token | JSON 응답 Body | 30분 | API 인가 |
| Refresh Token | HTTP-only Cookie | 7일 | Access Token 재발급 |

Access Token을 사용하는 API는 다음 헤더를 포함한다.

```http
Authorization: Bearer {access_token}
```

JWT Payload에는 최소 식별 정보인 `user_id`만 저장한다.

```json
{
  "user_id": 1
}
```

### 공통 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

## 3. Enum 정의

### 부서

| 값 | 설명 |
| --- | --- |
| `RESEARCH` | 연구 |
| `MEDICAL` | 의료 |
| `DEV` | 개발 |

### 성별

| 값 | 설명 |
| --- | --- |
| `M` | 남성 |
| `F` | 여성 |

### 권한

| 값 | 설명 |
| --- | --- |
| `PENDING` | 대기자, 마이페이지 외 모든 서비스 접근 불가 |
| `STAFF` | 스태프, 내부 직원으로 흉부 X-Ray 관련 읽기/쓰기/수정 가능 |
| `ADMIN` | 어드민, 시스템 관리자로 모든 데이터 접근 가능 |

## 4. API 목록

| 요구사항 ID | 기능 | Method | Endpoint | 인증 | 권한 |
| --- | --- | --- | --- | --- | --- |
| REQ-USER-001 | 회원가입 | `POST` | `/users/signup` | 불필요 | 전체 |
| REQ-USER-002 | 로그인 | `POST` | `/users/login` | 불필요 | 전체 |
| NFR-USER-001 | Access Token 재발급 | `POST` | `/users/refresh` | Refresh Token 필요 | 로그인 사용자 |
| REQ-USER-003 | 로그아웃 | `POST` | `/users/logout` | 필요 | 로그인 사용자 |
| REQ-USER-004 | 회원 목록 조회 | `GET` | `/admin/users` | 필요 | `ADMIN` |
| REQ-USER-005 | 회원 권한 변경 | `PATCH` | `/admin/users/role` | 필요 | `ADMIN` |
| REQ-USER-006 | 마이페이지 조회 | `GET` | `/users/me` | 필요 | 로그인 사용자 |
| REQ-USER-007 | 회원 정보 수정 | `PATCH` | `/users/me` | 필요 | 로그인 사용자 |
| REQ-USER-008 | 비밀번호 변경 | `PATCH` | `/users/me/password` | 필요 | 로그인 사용자 |
| REQ-USER-009 | 회원 탈퇴 | `DELETE` | `/users/me` | 필요 | 로그인 사용자 |

## 5. API 상세 명세

### 5.1 회원가입

사내 의료인, 개발 실무진, 연구진은 회원가입을 통해 서비스를 이용할 수 있다. 회원가입 직후 기본 권한은 `PENDING`으로 설정한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-001 |
| Method | `POST` |
| Endpoint | `/users/signup` |
| 인증 | 불필요 |

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678"
}
```

#### Request Field

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `email` | string | 예 | 이메일, 중복 불가 |
| `password` | string | 예 | 비밀번호 |
| `name` | string | 예 | 이름 |
| `department` | string | 예 | `RESEARCH`, `MEDICAL`, `DEV` |
| `gender` | string | 예 | `M`, `F` |
| `phone_number` | string | 예 | 휴대폰 번호, 중복 불가 |

#### Response `201 Created`

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "PENDING",
  "is_active": true
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `400 Bad Request` | 이메일 또는 휴대폰 번호가 중복된 경우 |
| `422 Unprocessable Entity` | 입력값 형식이 올바르지 않은 경우 |

### 5.2 로그인

회원가입을 완료한 사용자는 이메일과 비밀번호로 로그인할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-002, NFR-USER-001 |
| Method | `POST` |
| Endpoint | `/users/login` |
| 인증 | 불필요 |

#### Request Form Data

```text
username=user@example.com
password=Password123!
```

#### Response `200 OK`

```json
{
  "access_token": "access.jwt.token",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "홍길동",
    "department": "MEDICAL",
    "gender": "M",
    "phone_number": "01012345678",
    "role": "STAFF",
    "is_active": true
  }
}
```

Refresh Token은 클라이언트 JavaScript에서 접근할 수 없도록 HTTP-only Cookie로 전달한다.

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 이메일 또는 비밀번호가 일치하지 않는 경우 |
| `403 Forbidden` | 비활성화 계정인 경우 |

### 5.3 Access Token 재발급

Access Token이 만료되면 Refresh Token을 통해 Access Token을 재발급한다. Refresh Token도 만료되면 재로그인을 유도한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | NFR-USER-001 |
| Method | `POST` |
| Endpoint | `/users/refresh` |
| 인증 | HTTP-only Refresh Token Cookie 필요 |

#### Response `200 OK`

```json
{
  "access_token": "new.access.jwt.token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | Refresh Token이 없거나 만료된 경우 |

### 5.4 로그아웃

로그인 유저는 헤더에 노출되는 로그아웃 버튼을 통해 로그아웃할 수 있다. 로그아웃 후 로그인 페이지로 이동한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-003 |
| Method | `POST` |
| Endpoint | `/users/logout` |
| 인증 | 필요 |

#### Response `200 OK`

```json
{
  "message": "로그아웃되었습니다."
}
```

서버는 Refresh Token Cookie를 만료 처리한다.

### 5.5 회원 목록 조회

관리자 권한 유저는 모든 회원을 목록으로 조회할 수 있다. 이메일 또는 이름 검색, 부서별 필터링을 지원한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-004 |
| Method | `GET` |
| Endpoint | `/admin/users` |
| 인증 | 필요 |
| 권한 | `ADMIN` |

#### Query Parameter

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `query` | string | 아니오 | 이메일 또는 이름 검색어 |
| `department` | string | 아니오 | 부서 필터 |
| `page` | integer | 아니오 | 페이지 번호 |
| `size` | integer | 아니오 | 페이지 크기 |

#### Response `200 OK`

```json
{
  "total": 1,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "홍길동",
      "department": "MEDICAL",
      "gender": "M",
      "phone_number": "01012345678",
      "is_active": true,
      "role": "STAFF"
    }
  ]
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 로그인하지 않은 경우 |
| `403 Forbidden` | 관리자 권한이 없는 경우 |

### 5.6 회원 권한 변경

관리자 권한 유저는 선택한 회원의 권한을 변경할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-005 |
| Method | `PATCH` |
| Endpoint | `/admin/users/role` |
| 인증 | 필요 |
| 권한 | `ADMIN` |

#### Request Body

```json
{
  "user_id": 2,
  "new_role": "STAFF"
}
```

#### Request Field

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `user_id` | integer | 예 | 권한 변경 대상자 ID |
| `new_role` | string | 예 | `PENDING`, `STAFF`, `ADMIN` |

#### Response `200 OK`

```json
{
  "id": 2,
  "email": "staff@example.com",
  "name": "장문복",
  "role": "STAFF"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 로그인하지 않은 경우 |
| `403 Forbidden` | 관리자 권한이 없는 경우 |
| `404 Not Found` | 대상 회원이 존재하지 않는 경우 |
| `422 Unprocessable Entity` | 권한 값이 올바르지 않은 경우 |

### 5.7 마이페이지 조회

모든 로그인 유저는 마이페이지에서 본인의 정보를 조회할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-006 |
| Method | `GET` |
| Endpoint | `/users/me` |
| 인증 | 필요 |

#### Response `200 OK`

```json
{
  "name": "홍길동",
  "email": "user@example.com",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "STAFF"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 로그인하지 않은 경우 |

### 5.8 회원 정보 수정

모든 로그인 유저는 마이페이지에서 본인의 부서와 휴대폰 번호를 수정할 수 있다. 수정은 Partial Update 방식으로 처리한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-007 |
| Method | `PATCH` |
| Endpoint | `/users/me` |
| 인증 | 필요 |

#### Request Body

```json
{
  "department": "RESEARCH",
  "phone_number": "01098765432"
}
```

#### Request Field

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `department` | string | 아니오 | `RESEARCH`, `MEDICAL`, `DEV` |
| `phone_number` | string | 아니오 | 휴대폰 번호, 중복 불가 |

#### Response `200 OK`

```json
{
  "name": "홍길동",
  "email": "user@example.com",
  "department": "RESEARCH",
  "gender": "M",
  "phone_number": "01098765432",
  "role": "STAFF"
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `400 Bad Request` | 수정할 항목이 없거나 휴대폰 번호가 중복된 경우 |
| `401 Unauthorized` | 로그인하지 않은 경우 |
| `422 Unprocessable Entity` | 입력값 형식이 올바르지 않은 경우 |

### 5.9 비밀번호 변경

모든 로그인 유저는 기존 비밀번호를 검증한 뒤 새로운 비밀번호로 변경할 수 있다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-008 |
| Method | `PATCH` |
| Endpoint | `/users/me/password` |
| 인증 | 필요 |

#### Request Body

```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword123!"
}
```

#### Response `200 OK`

```json
{
  "message": "비밀번호가 변경되었습니다."
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `400 Bad Request` | 기존 비밀번호가 일치하지 않거나 새 비밀번호 정책이 맞지 않는 경우 |
| `401 Unauthorized` | 로그인하지 않은 경우 |

### 5.10 회원 탈퇴

모든 로그인 유저는 마이페이지에서 회원탈퇴를 진행할 수 있다. 회원탈퇴 시 Database에서 회원과 관련된 정보를 모두 즉시 삭제한다.

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-USER-009 |
| Method | `DELETE` |
| Endpoint | `/users/me` |
| 인증 | 필요 |

#### Response `200 OK`

```json
{
  "message": "회원 탈퇴가 완료되었습니다."
}
```

#### Error

| Status | 상황 |
| --- | --- |
| `401 Unauthorized` | 로그인하지 않은 경우 |

## 6. 비기능 요구사항 반영

### NFR-USER-001 인증 / 인가

- 로그인 시 JWT를 발급한다.
- Access Token 만료 시간은 30분이다.
- Refresh Token 만료 시간은 7일이다.
- Access Token 만료 시 Refresh Token으로 재발급한다.
- Refresh Token도 만료되면 재로그인을 유도한다.
- Refresh Token은 HTTP-only Cookie로 전달한다.
- JWT Payload에는 `user_id`만 저장한다.

### NFR-USER-002 비밀번호 입력 보안

- 모든 비밀번호 입력창은 기본적으로 마스킹 처리한다.
- 비밀번호 보기 아이콘을 클릭하면 입력한 비밀번호를 확인할 수 있다.
- 서버는 비밀번호를 평문으로 저장하지 않고 해시값으로 저장한다.

### NFR-USER-003 API 성능

- 모든 User API는 최대 3초 이내에 로직을 처리하고 응답해야 한다.
- DB 조회 시 필요한 조건 검색과 인덱스 사용을 고려한다.
- 회원 목록 조회는 페이지네이션을 적용하여 응답 크기를 제한한다.

## 7. 테스트 시나리오

| 번호 | 테스트 항목 | 기대 결과 |
| --- | --- | --- |
| 1 | 올바른 정보로 회원가입 | `201 Created` |
| 2 | 중복 이메일로 회원가입 | `400 Bad Request` |
| 3 | 이메일과 비밀번호로 로그인 | Access Token 발급 |
| 4 | 잘못된 비밀번호로 로그인 | `401 Unauthorized` |
| 5 | Access Token 만료 후 Refresh Token으로 재발급 | 새 Access Token 발급 |
| 6 | 로그인 후 로그아웃 | Refresh Token Cookie 만료 |
| 7 | 로그인 후 마이페이지 조회 | 본인 정보 반환 |
| 8 | 부서 또는 휴대폰 번호 수정 | 수정된 정보 반환 |
| 9 | 기존 비밀번호 확인 후 비밀번호 변경 | 성공 메시지 반환 |
| 10 | 일반 사용자가 관리자 회원 목록 조회 | `403 Forbidden` |
| 11 | 관리자가 회원 목록 검색/필터 조회 | 조건에 맞는 회원 목록 반환 |
| 12 | 관리자가 회원 권한 변경 | 변경된 권한 반환 |
| 13 | 회원 탈퇴 | 회원 관련 정보 즉시 삭제 |

## 8. 정리

User API는 회원가입부터 로그인, JWT 인증/인가, 마이페이지, 관리자 회원 관리까지 사용자 관련 기능의 기준이 된다.

이번 설계에서는 요구사항 정의서의 `REQ-USER-001`부터 `REQ-USER-009`, `NFR-USER-001`부터 `NFR-USER-003`까지를 API 명세에 반영했다.
