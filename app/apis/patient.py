from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.patient import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.services.patient import (
    create_patient,
    delete_patient,
    get_patient,
    list_patients,
    update_patient,
)


router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_api(
    data: PatientCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await create_patient(db, current_user, data)


@router.get("", response_model=list[PatientResponse])
async def list_patients_api(
    name: str | None = None,
    gender: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await list_patients(db, current_user, name, gender, min_age, max_age)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_api(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await get_patient(db, current_user, patient_id)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient_api(
    patient_id: int,
    data: PatientUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await update_patient(db, current_user, patient_id, data)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_api(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    await delete_patient(db, current_user, patient_id)
