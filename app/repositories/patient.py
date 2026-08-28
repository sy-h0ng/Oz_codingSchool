from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import GenderEnum
from app.models.patient import Patient


async def create_patient(db: AsyncSession, **kwargs) -> Patient:
    patient = Patient(**kwargs)
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def list_patients(
    db: AsyncSession,
    name: str | None = None,
    gender: GenderEnum | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[Patient]:
    stmt = select(Patient).order_by(Patient.id.desc())

    if name:
        stmt = stmt.where(Patient.name.ilike(f"%{name}%"))
    if gender:
        stmt = stmt.where(Patient.gender == gender)
    if min_age is not None:
        stmt = stmt.where(Patient.age >= min_age)
    if max_age is not None:
        stmt = stmt.where(Patient.age <= max_age)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_patient(db: AsyncSession, patient: Patient, **fields) -> Patient:
    for key, value in fields.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def delete_patient(db: AsyncSession, patient: Patient) -> None:
    await db.delete(patient)
    await db.commit()
