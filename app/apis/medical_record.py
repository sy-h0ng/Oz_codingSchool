from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.medical_record import MedicalRecordListItem, MedicalRecordResponse
from app.services.medical_record import (
    create_medical_record,
    get_medical_record,
    list_medical_records,
)

router = APIRouter(prefix="/api/v1", tags=["medical-records"])


@router.post(
    "/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="진료기록 등록 (REQ-MDR-001)",
)
async def create_medical_record_api(
    patient_id: Annotated[int, Form()],
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptoms: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """STAFF/ADMIN 권한을 가진 유저가 환자의 흉부 X-Ray 이미지를 포함한 진료기록을
    등록한다. `patient_id`가 존재하지 않으면 404, `chart_number`가 이미 사용 중이면
    409를 반환한다."""
    return await create_medical_record(
        db, current_user, patient_id, chart_number, symptoms, xray_image
    )


@router.get(
    "/patients/{patient_id}/medical-records",
    response_model=list[MedicalRecordListItem],
    summary="환자별 진료기록 목록 조회 (REQ-MDR-002)",
)
async def list_medical_records_api(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """해당 환자의 진료기록을 최신순으로 조회한다. `symptoms`는 100자를 넘으면
    말줄임 처리되어 내려간다."""
    return await list_medical_records(db, current_user, patient_id)


@router.get(
    "/medical-records/{record_id}",
    response_model=MedicalRecordResponse,
    summary="진료기록 상세 조회 (REQ-MDR-003)",
)
async def get_medical_record_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """진료기록 1건의 상세 정보(증상 전문, 최신 X-Ray 이미지 URL 포함)를 조회한다."""
    return await get_medical_record(db, current_user, record_id)
