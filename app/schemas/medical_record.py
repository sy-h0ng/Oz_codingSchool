from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

SYMPTOMS_SUMMARY_MAX_LENGTH = 100


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_image_url: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class MedicalRecordListItem(BaseModel):
    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("symptoms")
    @classmethod
    def truncate_symptoms(cls, value: str) -> str:
        if len(value) > SYMPTOMS_SUMMARY_MAX_LENGTH:
            return value[:SYMPTOMS_SUMMARY_MAX_LENGTH] + "..."
        return value
