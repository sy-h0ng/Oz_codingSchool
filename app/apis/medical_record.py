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
    delete_medical_record,
    get_medical_record,
    list_medical_records,
    update_medical_record,
)

router = APIRouter(prefix="/api/v1", tags=["medical-records"])


@router.post(
    "/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record_api(
    patient_id: Annotated[int, Form()],
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptoms: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await create_medical_record(
        db, current_user, patient_id, chart_number, symptoms, xray_image
    )


@router.get("/patients/{patient_id}/medical-records", response_model=list[MedicalRecordListItem])
async def list_medical_records_api(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await list_medical_records(db, current_user, patient_id)


@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await get_medical_record(db, current_user, record_id)


@router.patch("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record_api(
    record_id: int,
    chart_number: Annotated[str | None, Form(min_length=1, max_length=50)] = None,
    symptoms: Annotated[str | None, Form(min_length=1)] = None,
    xray_image: Annotated[UploadFile | None, File()] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await update_medical_record(
        db, current_user, record_id, chart_number, symptoms, xray_image
    )


@router.delete("/medical-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_record_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    await delete_medical_record(db, current_user, record_id)
