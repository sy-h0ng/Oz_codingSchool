import re

from pydantic import BaseModel, Field, field_validator

from app.models.enums import DepartmentEnum, GenderEnum, RoleEnum


class UserSignupRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8)
    name: str = Field(max_length=20)
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str = Field(max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if (not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v)
                or not re.search(r"\d", v) or not re.search(r"[^a-zA-Z0-9]", v)):
            raise ValueError("비밀번호는 대소문자, 숫자, 특수문자를 각 1개씩 포함해야 합니다.")
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str
    role: RoleEnum

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserUpdateRequest(BaseModel):
    department: DepartmentEnum | None = None
    phone_number: str | None = Field(default=None, max_length=20)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if (not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v)
                or not re.search(r"\d", v) or not re.search(r"[^a-zA-Z0-9]", v)):
            raise ValueError("비밀번호는 대소문자, 숫자, 특수문자를 각 1개씩 포함해야 합니다.")
        return v

class AdminUserListItem(BaseModel):
    id: int
    email: str
    name: str
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True


class RoleUpdateRequest(BaseModel):
    user_id: int
    new_role: RoleEnum