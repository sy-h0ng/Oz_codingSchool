from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import GenderEnum, RoleEnum
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient import (
    create_patient as repo_create_patient,
    delete_patient as repo_delete_patient,
    get_patient_by_id,
    list_patients as repo_list_patients,
    update_patient as repo_update_patient,
)
from app.schemas.patient import PatientCreateRequest, PatientResponse, PatientUpdateRequest


def require_patient_access(user: User) -> None:
    role = user.role.value if isinstance(user.role, RoleEnum) else str(user.role)
    if role not in (RoleEnum.STAFF.value, RoleEnum.ADMIN.value, "staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="환자 관리 기능을 사용할 권한이 없습니다.",
        )


def request_gender_to_model(gender: str) -> GenderEnum:
    if gender == "male":
        return GenderEnum.M
    if gender == "female":
        return GenderEnum.F
    raise HTTPException(status_code=422, detail="올바른 성별 값이 아닙니다.")


def model_gender_to_response(gender: GenderEnum | None) -> str:
    gender_value = gender.value if isinstance(gender, GenderEnum) else str(gender)
    if gender_value in (GenderEnum.M.value, "male"):
        return "male"
    return "female"


def to_patient_response(patient: Patient) -> PatientResponse:
    return PatientResponse(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        gender=model_gender_to_response(patient.gender),
        phone_number=patient.phone,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


async def create_patient(
    db: AsyncSession,
    current_user: User,
    data: PatientCreateRequest,
) -> PatientResponse:
    require_patient_access(current_user)
    patient = await repo_create_patient(
        db,
        name=data.name,
        age=data.age,
        gender=request_gender_to_model(data.gender),
        phone=data.phone_number,
    )
    return to_patient_response(patient)


async def list_patients(
    db: AsyncSession,
    current_user: User,
    name: str | None,
    gender: str | None,
    min_age: int | None,
    max_age: int | None,
) -> list[PatientResponse]:
    require_patient_access(current_user)

    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status_code=400, detail="최소 나이는 최대 나이보다 클 수 없습니다.")

    model_gender = request_gender_to_model(gender) if gender else None
    patients = await repo_list_patients(
        db,
        name=name,
        gender=model_gender,
        min_age=min_age,
        max_age=max_age,
    )
    return [to_patient_response(patient) for patient in patients]


async def get_patient(
    db: AsyncSession,
    current_user: User,
    patient_id: int,
) -> PatientResponse:
    require_patient_access(current_user)
    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")
    return to_patient_response(patient)


async def update_patient(
    db: AsyncSession,
    current_user: User,
    patient_id: int,
    data: PatientUpdateRequest,
) -> PatientResponse:
    require_patient_access(current_user)
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 항목을 최소 하나 이상 입력해야 합니다.")

    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")

    if "phone_number" in updates:
        updates["phone"] = updates.pop("phone_number")

    updated_patient = await repo_update_patient(db, patient, **updates)
    return to_patient_response(updated_patient)


async def delete_patient(
    db: AsyncSession,
    current_user: User,
    patient_id: int,
) -> None:
    require_patient_access(current_user)
    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")
    await repo_delete_patient(db, patient)
