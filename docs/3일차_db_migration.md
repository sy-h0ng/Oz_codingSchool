# 3일차. DB 모델 작성 & Migration

Stage 3 - "DB 모델 작성" 과제로 작성한 문서입니다. [ERD (dbdiagram)](https://dbdiagram.io/d/ai_health_assignment-69d5f55f808962968443c041)를 기준으로 `app/models/`에 SQLAlchemy ORM 모델을 작성하고, Alembic으로 마이그레이션을 생성·적용한 과정을 정리합니다.

## 1. ERD 요약

| 테이블 | 설명 |
| --- | --- |
| `users` | 내부 사용자(개발팀/의료진/연구진) 계정. 회원가입 시 `role`은 `PENDING`이며 관리자가 `STAFF`/`ADMIN`으로 승인합니다. |
| `patients` | 진료 대상 환자 정보 |
| `medical_records` | 환자의 진료 기록(차트). `patients`를 참조(FK) |
| `xray_images` | 진료 기록에 첨부되는 X-Ray 이미지. `medical_records`, `users`(업로더)를 참조(FK) |
| `ai_analysis_results` | 진료 기록에 대한 AI 폐렴 예측 결과. `medical_records`를 참조(FK) |

Enum 정의: `gender(M, F)`, `role(PENDING, STAFF, ADMIN)`, `department(MEDICAL, DEV, RESEARCH)` → `app/models/enums.py`에 `str, enum.Enum`으로 정의하고, SQLAlchemy 컬럼에서는 `Enum(..., native_enum=False)`로 사용해 이식성 있는 `VARCHAR` 컬럼으로 저장했습니다.

## 2. 구현 파일

- `app/models/enums.py` — `GenderEnum`, `RoleEnum`, `DepartmentEnum`
- `app/models/user.py` — `User` (`users` 테이블)
- `app/models/patient.py` — `Patient` (`patients` 테이블)
- `app/models/medical_record.py` — `MedicalRecord` (`medical_records` 테이블)
- `app/models/xray_image.py` — `XrayImage` (`xray_images` 테이블)
- `app/models/ai_analysis_result.py` — `AIAnalysisResult` (`ai_analysis_results` 테이블)
- `app/models/__init__.py` — 위 모델들을 전부 import하여 Alembic autogenerate가 인식하도록 등록
- `alembic/versions/45d9d061825c_add_users_patients_medical_records_xray_.py` — 5개 테이블을 생성하는 마이그레이션

### 설계 시 주의했던 점 / ERD와 다르게 처리한 부분

ERD에는 `users.id`가 `integer`, `xray_images.uploader_id`가 `bigint`로 표기되어 있는데, MySQL은 **FK로 연결되는 두 컬럼의 타입이 정확히 일치해야** 외래키 제약조건을 만들 수 있습니다. 그대로 구현하면 아래처럼 마이그레이션이 실패합니다.

```
sqlalchemy.exc.OperationalError: (1005, "Can't create table `ai_health`.`xray_images`
(errno: 150 "Foreign key constraint is incorrectly formed")")
```

그래서 `uploader_id`를 참조 대상인 `users.id`와 동일한 `Integer`로 맞춰서 정의했습니다. (`app/models/xray_image.py` 주석 참고)

## 3. 마이그레이션 생성 & 적용 절차

```bash
# 1) 모델 작성 후, autogenerate로 리비전 파일 생성
uv run alembic revision --autogenerate -m "add users, patients, medical_records, xray_images, ai_analysis_results tables"

# 2) 생성된 리비전 파일 검토 (op.create_table 5개, FK/UNIQUE 제약조건 확인)

# 3) 실제 DB에 적용
uv run alembic upgrade head
```

로컬 검증용 DB(MySQL 호환)에 위 과정을 그대로 실행해 5개 테이블이 정상적으로 생성되는 것과, FK/UNIQUE 제약조건이 의도대로 걸리는 것까지 확인했습니다.

```
$ uv run alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 45d9d061825c,
  add users, patients, medical_records, xray_images, ai_analysis_results tables
```

```
mysql> USE ai_health; SHOW TABLES;
+----------------------+
| Tables_in_ai_health  |
+----------------------+
| ai_analysis_results  |
| alembic_version      |
| medical_records      |
| patients             |
| users                |
| xray_images          |
+----------------------+
```

`alembic_version` 테이블에 현재 리비전(`45d9d061825c`)이 기록되어 있는 것도 확인했습니다.

## 4. DB Viewer로 스키마 확인한 화면

로컬에 MySQL 8.0을 설치하고 `.env`를 연결한 뒤 `uv run alembic upgrade head`를 실행했고, MySQL Workbench로 접속해 `ai_health` 스키마 아래 5개 테이블(+ `alembic_version`)이 정상적으로 생성된 것을 확인했습니다.

![DB 스키마 적용 결과](./images/3일차_db_schema.png)
