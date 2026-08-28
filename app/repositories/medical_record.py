from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.xray_image import XrayImage


async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    """environment 상 app/repositories/patient.py(feat/patient-apis)와 병합 시
    동일 시그니처의 함수로 교체 가능한, 환자 존재 확인용 최소 조회 함수."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def create_medical_record(db: AsyncSession, **kwargs) -> MedicalRecord:
    record = MedicalRecord(**kwargs)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_medical_record_by_id(db: AsyncSession, record_id: int) -> MedicalRecord | None:
    # populate_existing=True: 같은 세션에서 이미 로드된 인스턴스라도
    # xray_images 등 연관 컬렉션을 최신 상태로 다시 채운다.
    stmt = (
        select(MedicalRecord)
        .options(selectinload(MedicalRecord.xray_images))
        .where(MedicalRecord.id == record_id)
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_medical_record_by_chart_number(
    db: AsyncSession, chart_number: str
) -> MedicalRecord | None:
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.chart_number == chart_number)
    )
    return result.scalar_one_or_none()


async def list_medical_records_by_patient(
    db: AsyncSession, patient_id: int
) -> list[MedicalRecord]:
    stmt = (
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_xray_image(db: AsyncSession, **kwargs) -> XrayImage:
    xray_image = XrayImage(**kwargs)
    db.add(xray_image)
    await db.commit()
    await db.refresh(xray_image)
    return xray_image
