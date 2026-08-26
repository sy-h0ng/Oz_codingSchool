# 3일차 DB Migration

## 1. 진행 목표

ERD를 참고하여 SQLAlchemy ORM 모델을 작성하고, Alembic 마이그레이션을 통해 MySQL 데이터베이스에 스키마를 반영한다.

이번 단계에서 사용한 데이터베이스는 **MySQL**이다.

## 2. ERD 기준 테이블

ERD에는 다음 5개의 테이블이 있다.

| 테이블명 | 역할 |
| --- | --- |
| `users` | 시스템 사용자 정보 저장 |
| `patients` | 환자 기본 정보 저장 |
| `medical_records` | 환자의 진료 기록 저장 |
| `xray_images` | 진료 기록에 연결된 X-Ray 이미지 정보 저장 |
| `ai_analysis_results` | AI 폐렴 분석 결과 저장 |

## 3. 작성한 SQLAlchemy 모델 파일

각 모델은 `app/models/` 하위에 테이블별로 분리하여 작성했다.

| 모델 파일 | SQLAlchemy 클래스 | 연결 테이블 |
| --- | --- | --- |
| `app/models/user.py` | `User` | `users` |
| `app/models/patient.py` | `Patient` | `patients` |
| `app/models/medical_record.py` | `MedicalRecord` | `medical_records` |
| `app/models/xray_image.py` | `XrayImage` | `xray_images` |
| `app/models/ai_analysis_result.py` | `AiAnalysisResult` | `ai_analysis_results` |

그리고 Alembic이 모델을 인식할 수 있도록 `app/models/__init__.py`에서 모델 클래스를 import했다.

```python
from app.models.ai_analysis_result import AiAnalysisResult
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.models.xray_image import XrayImage
```

## 4. 테이블 관계

ERD 기준 관계는 다음과 같다.

| 관계 | 설명 |
| --- | --- |
| `patients.id` → `medical_records.patient_id` | 한 명의 환자는 여러 진료 기록을 가질 수 있다. |
| `medical_records.id` → `xray_images.record_id` | 하나의 진료 기록은 여러 X-Ray 이미지를 가질 수 있다. |
| `users.id` → `xray_images.uploader_id` | 사용자는 X-Ray 이미지를 업로드할 수 있다. |
| `medical_records.id` → `ai_analysis_results.record_id` | 하나의 진료 기록은 AI 분석 결과와 연결된다. |

## 5. 마이그레이션 파일

작성한 Alembic 마이그레이션 파일은 다음과 같다.

```text
alembic/versions/20260826_143000_create_ai_health_tables.py
```

이 마이그레이션 파일은 다음 테이블을 생성한다.

```text
users
patients
medical_records
xray_images
ai_analysis_results
```

또한 다음 외래키 제약 조건을 포함한다.

```text
medical_records.patient_id → patients.id ON DELETE CASCADE
xray_images.record_id → medical_records.id ON DELETE CASCADE
xray_images.uploader_id → users.id ON DELETE SET NULL
ai_analysis_results.record_id → medical_records.id ON DELETE CASCADE
```

## 6. MySQL 환경 설정

프로젝트의 `.env.example`을 기준으로 `.env` 파일을 생성하고 MySQL 접속 정보를 설정한다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=ozcoding
DB_PASSWORD=pw1234
DB_ROOT_PASSWORD=Password123@!
DB_NAME=ai_health
```

`app/core/config.py`는 `.env` 파일의 값을 읽고, `app/core/db/databases.py`는 이 값을 사용해 MySQL 접속 주소를 만든다.

예상 접속 주소는 다음과 같은 형태이다.

```text
mysql+asyncmy://ozcoding:pw1234@localhost:3306/ai_health
```

## 7. 마이그레이션 실행 방법

MySQL이 실행 중인 상태에서 아래 명령어로 마이그레이션을 적용한다.

```bash
alembic upgrade head
```

프로젝트 실행 환경에 따라 다음 명령어를 사용할 수도 있다.

```bash
python3 -m alembic upgrade head
```

또는 `uv`가 설치되어 있다면 다음 명령어를 사용한다.

```bash
uv run alembic upgrade head
```

## 8. DB Viewer 확인

마이그레이션 적용 후 DB Viewer에서 `ai_health` 데이터베이스를 열어 다음 테이블이 생성되었는지 확인한다.

```text
users
patients
medical_records
xray_images
ai_analysis_results
alembic_version
```

아래 영역에 DB Viewer 확인 이미지를 추가한다.

> DB Viewer에서 테이블 목록이 보이는 화면을 캡처하여 이 문서에 첨부한다.

![DB Viewer schema 확인 이미지](./images/3일차_db_schema.png)

## 9. 정리

이번 작업에서는 ERD를 기준으로 5개의 SQLAlchemy 모델을 작성했고, Alembic 마이그레이션 파일을 통해 MySQL에 테이블을 생성할 수 있도록 준비했다.

모델 파일과 마이그레이션 파일이 PR을 통해 `main` 또는 `develop` 브랜치에 merge되면 코드 제출 조건을 충족한다.  
이후 실제 MySQL DB에 마이그레이션을 적용하고 DB Viewer 캡처 이미지를 문서에 추가하면 최종 확인 조건까지 완료된다.
