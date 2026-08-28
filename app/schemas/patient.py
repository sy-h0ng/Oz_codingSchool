from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


PatientGender = Literal["male", "female"]


class PatientCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    age: int = Field(ge=0, le=130)
    gender: PatientGender
    phone_number: str = Field(min_length=10, max_length=13)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        only_digits = re.sub(r"\D", "", value)
        if not re.fullmatch(r"01[016789]\d{7,8}", only_digits):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
        return only_digits


class PatientUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone_number: str | None = Field(default=None, min_length=10, max_length=13)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return value
        only_digits = re.sub(r"\D", "", value)
        if not re.fullmatch(r"01[016789]\d{7,8}", only_digits):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
        return only_digits


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: PatientGender
    phone_number: str
    created_at: datetime
    updated_at: datetime | None = None


class PatientListResponse(PatientResponse):
    pass
