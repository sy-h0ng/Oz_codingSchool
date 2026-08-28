from __future__ import annotations

import uuid as uuid_pkg
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RoleEnum
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.repositories.medical_record import (
    create_medical_record as repo_create_medical_record,
    create_xray_image,
    get_medical_record_by_chart_number,
    get_medical_record_by_id,
    get_patient_by_id,
    list_medical_records_by_patient as repo_list_medical_records_by_patient,
)
from app.schemas.medical_record import MedicalRecordListItem, MedicalRecordResponse

BASE_DIR = Path(__file__).resolve().parent.parent.parent
XRAY_DIR = BASE_DIR / "media" / "xrays"
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}


def require_medical_record_access(user: User) -> None:
    role = user.role.value if isinstance(user.role, RoleEnum) else str(user.role)
    if role not in (RoleEnum.STAFF.value, RoleEnum.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="진료기록 관리 기능을 사용할 권한이 없습니다.",
        )


def _latest_xray_image_url(record: MedicalRecord) -> str | None:
    if not record.xray_images:
        return None
    latest = max(record.xray_images, key=lambda image: image.id)
    return latest.image_url


def to_medical_record_response(record: MedicalRecord) -> MedicalRecordResponse:
    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        xray_image_url=_latest_xray_image_url(record) or "",
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _save_xray_image(xray_image: UploadFile) -> str:
    if xray_image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="흉부 X-Ray 이미지는 JPEG 또는 PNG 형식만 업로드할 수 있습니다.",
        )
    XRAY_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(xray_image.filename or "").suffix
    stored_filename = f"{uuid_pkg.uuid4()}{extension}"
    destination = XRAY_DIR / stored_filename
    content = await xray_image.read()
    destination.write_bytes(content)
    return f"/media/xrays/{stored_filename}"


async def create_medical_record(
    db: AsyncSession,
    current_user: User,
    patient_id: int,
    chart_number: str,
    symptoms: str,
    xray_image: UploadFile,
) -> MedicalRecordResponse:
    require_medical_record_access(current_user)

    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환자를 찾을 수 없습니다.")

    if await get_medical_record_by_chart_number(db, chart_number):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 차트 번호입니다.")

    record = await repo_create_medical_record(
        db, patient_id=patient_id, chart_number=chart_number, symptoms=symptoms
    )

    image_url = await _save_xray_image(xray_image)
    await create_xray_image(
        db,
        record_id=record.id,
        uploader_id=current_user.id,
        image_url=image_url,
        shooting_datetime=datetime.now(UTC),
    )

    record = await get_medical_record_by_id(db, record.id)
    return to_medical_record_response(record)


async def list_medical_records(
    db: AsyncSession, current_user: User, patient_id: int
) -> list[MedicalRecordListItem]:
    require_medical_record_access(current_user)

    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환자를 찾을 수 없습니다.")

    records = await repo_list_medical_records_by_patient(db, patient_id)
    return [MedicalRecordListItem.model_validate(record) for record in records]


async def get_medical_record(
    db: AsyncSession, current_user: User, record_id: int
) -> MedicalRecordResponse:
    require_medical_record_access(current_user)
    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")
    return to_medical_record_response(record)

