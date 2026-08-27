import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import DepartmentEnum, GenderEnum, RoleEnum


class UserSignupRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=20)
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str = Field(..., min_length=10, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.match(pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호는 대문자를 1개 이상 포함해야 합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호는 소문자를 1개 이상 포함해야 합니다.")
        if not re.search(r"\d", value):
            raise ValueError("비밀번호는 숫자를 1개 이상 포함해야 합니다.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("비밀번호는 특수문자를 1개 이상 포함해야 합니다.")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        only_digits = re.sub(r"\D", "", value)
        if not re.fullmatch(r"01[016789]\d{7,8}", only_digits):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
        return only_digits


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
