# AI Health Web Assignment

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```

---

## 프로젝트 과정 총정리

AI Health는 흉부 X-Ray 이미지로 폐렴 예측을 돕는 웹 서비스입니다. 아래 내용은 `docs/`에 남긴 1~9일차 학습·구현 기록을 기준으로, 팀이 어떤 순서와 방식으로 프로젝트를 진행했는지 되돌아본 내용입니다.

### 1. Team Rule 정의

**참고: `docs/1일차_team_rules.md`**

프로젝트를 시작하며 팀이 함께 집중해서 당일 Stage를 마무리한다는 기본 약속을 정했습니다. 작은 규칙이지만, 협업에서는 각자 맡은 작업을 제때 공유하고 다음 작업자가 이어서 할 수 있게 만드는 출발점이 되었습니다.

### 2. 사용자 요구사항 정의

**참고: `docs/4일차_USER_API_설계.md`**

사용자 요구사항을 먼저 읽고, 회원 기능을 실제 화면과 API로 바꾸었습니다.

- 회원가입: 이메일, 비밀번호, 이름, 부서, 성별, 연락처 입력
- 로그인·로그아웃과 JWT 기반 인증
- 마이페이지 조회, 부서·연락처 부분 수정, 비밀번호 변경, 회원 탈퇴
- 관리자 회원 목록 조회, 이름·이메일 검색과 부서 필터, 권한 변경

요구사항에서 “누가 할 수 있는가”, “어떤 값을 입력하는가”, “무엇을 반환하는가”를 찾아 API 설계의 기준으로 삼았습니다.

### 3. API 명세서 작성

**참고: `docs/4일차_USER_API_설계.md`, `docs/7일차_앱_실행화면.md`**

요구사항을 HTTP 메서드와 주소로 나누어 명세화했습니다. 회원 API는 가입·로그인·내 정보·관리자 기능으로, 이후 환자·진료기록·AI 예측 API는 각 도메인별 기능으로 분리했습니다.

- `POST /api/v1/users/signup`, `POST /login`, `POST /logout`
- `GET/PATCH/DELETE /api/v1/users/me`, `PATCH /me/password`
- `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/role`
- 환자 CRUD·검색/필터, 진료기록 등록·목록·상세, AI 예측·분석 결과 조회

명세를 먼저 정리했기 때문에 프론트엔드에서 어떤 Header, 요청 본문, 응답 데이터를 보내고 받아야 하는지 확인할 수 있었습니다.

### 4. Git & GitHub Branch 전략 구성

**참고: `docs/2일차_git_branch_전략.md`**

Git Flow와 GitHub Flow를 비교한 뒤, 학습 프로젝트에는 단순한 **GitHub Flow**를 사용하기로 했습니다.

- `main`은 항상 동작 가능한 안정 브랜치로 유지
- 기능별 브랜치에서 작업 후 커밋·push
- Pull Request를 만들고 검토한 뒤 `main`에 병합
- 브랜치 이름은 `feature/*`, `docs/*`, `fix/*`, `style/*`처럼 목적을 드러내기
- 커밋 메시지도 `feat`, `fix`, `docs`, `style` 접두어로 변경 성격을 구분

이 방식으로 여러 사람이 만든 변경을 바로 `main`에 섞지 않고, PR 단위로 확인하며 합칠 수 있었습니다.

### 5. 프로젝트 세팅

**참고: `docs/3일차_프로젝트_뜯어보기.md`, `docs/3일차_db_migration.md`**

제공된 FastAPI 템플릿의 역할을 먼저 파악했습니다. 요청은 `apis`에서 받고, 업무 규칙은 `services`, DB 접근은 `repositories`, 데이터 검증은 `schemas`, 테이블 정의는 `models`가 맡도록 나뉘어 있었습니다.

MySQL과 SQLAlchemy 비동기 연결을 설정하고, ERD를 바탕으로 아래 테이블을 모델로 만들었습니다.

- `users`
- `patients`
- `medical_records`
- `xray_images`
- `ai_analysis_results`

그다음 `model 작성 → app/models/__init__.py import → Alembic 자동 마이그레이션 생성 → 검토 → upgrade head` 순서로 스키마를 반영하고 DB Viewer에서 생성 결과를 확인했습니다.

### 6. API 및 AI 모델 코드 작성 후 병합

**참고: `docs/4일차_USER_API_설계.md`, `docs/7일차_앱_실행화면.md`**

기능은 책임에 따라 `apis`, `services`, `repositories`, `schemas`, `models`로 나누어 구현했습니다. 회원 API에 JWT 인증을 연결한 뒤, 환자 등록·검색·수정·삭제와 진료기록 등록·조회 기능을 추가했습니다.

진료기록 등록은 `multipart/form-data`로 X-Ray 이미지를 받아 `media/xray/`에 저장하도록 했고, 같은 차트 번호는 `409 Conflict`로 처리했습니다. 저장된 X-Ray를 AI 모델에 전달해 예측하고, 예측 결과와 분석 이력을 조회하는 흐름까지 연결했습니다. 각 기능은 담당 브랜치에서 작업하고 PR을 통해 병합했습니다.

### 7. 아키텍처 설계 및 적용

**참고: `docs/9일차_동시성문제_해결을위한_아키텍처설계.md`**

AI 추론을 FastAPI 요청 처리 안에서 바로 수행하면, 여러 요청이 동시에 들어왔을 때 서버가 느려지고 같은 이미지가 중복 추론될 수 있습니다. 이를 해결하기 위한 Event-Driven Architecture를 설계했습니다.

```text
사용자 → FastAPI → Redis Lock / 작업 이벤트 → Redis Stream → AI Worker
       ← FastAPI ← 결과 이벤트            ← Redis Pub/Sub ← AI Worker
                         ↓
                       MySQL
```

핵심은 FastAPI가 요청 접수와 결과 저장을 맡고, AI Worker가 무거운 추론만 맡도록 분리하는 것입니다. Redis Lock으로 중복 요청을 막고, 작업 큐·Consumer Group·재시도/DLQ 같은 구조로 여러 워커와 실패 복구까지 고려했습니다. 같은 진료기록과 모델로 저장된 결과가 있으면 DB의 기존 결과를 먼저 반환하는 방향도 정했습니다.

### 8. Docker 인프라 관련 파일 작성

**참고: `docs/8일차_Docker_실행화면.md`**

로컬마다 다른 개발 환경 문제를 줄이기 위해 Docker로 FastAPI와 MySQL을 함께 실행했습니다.

- `app/Dockerfile`로 FastAPI 이미지를 생성
- `docker-compose.yml`로 FastAPI·MySQL 서비스를 함께 정의
- 컨테이너 내부에서는 MySQL 주소를 `mysql:3306`으로 사용
- 로컬의 3306 포트가 사용 중이어서 MySQL 외부 포트는 `3307`로 변경
- `docker compose up --build`, `docker compose ps`로 이미지 빌드와 컨테이너 상태 확인

이를 통해 팀원이 같은 명령어로 유사한 실행 환경을 만들 수 있었습니다.
