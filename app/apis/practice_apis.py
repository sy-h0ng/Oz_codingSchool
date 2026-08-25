import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/practice_api", tags=["practice_api"])

user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!",
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!",
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@",
    },
]


def validate_password(password: str) -> str:
    if not 8 <= len(password) <= 20:
        raise ValueError("비밀번호는 8자 이상 20자 이하이어야 합니다.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("비밀번호에는 대문자가 최소 1개 포함되어야 합니다.")
    if not re.search(r"[a-z]", password):
        raise ValueError("비밀번호에는 소문자가 최소 1개 포함되어야 합니다.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("비밀번호에는 특수문자가 최소 1개 포함되어야 합니다.")
    return password


def validate_email(email: str) -> str:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if len(email) > 30 or not re.match(pattern, email):
        raise ValueError("올바른 이메일 형식이 아니거나 30자를 초과했습니다.")
    return email


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=10)
    age: int = Field(..., ge=14)
    email: str = Field(..., max_length=30)
    password: str = Field(..., min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return validate_email(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password(value)


class UserUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=14)
    email: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = Field(None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return validate_email(value)
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            return validate_password(value)
        return value


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "age": user["age"],
        "email": user["email"],
    }


def find_user(user_id: int) -> dict:
    for user in user_list:
        if user["id"] == user_id:
            return user

    raise HTTPException(status_code=404, detail="존재하지 않는 회원입니다.")


@router.get("/users")
def get_users():
    return [public_user(user) for user in user_list]


@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = find_user(user_id)
    return public_user(user)


@router.post("/users", status_code=201)
def create_user(user_data: UserCreate):
    for user in user_list:
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    new_id = max(user["id"] for user in user_list) + 1 if user_list else 1
    new_user = {
        "id": new_id,
        "name": user_data.name,
        "age": user_data.age,
        "email": user_data.email,
        "password": user_data.password,
    }

    user_list.append(new_user)

    return public_user(new_user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, user_data: UserUpdate):
    user = find_user(user_id)
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    if "email" in update_data:
        for existing_user in user_list:
            if existing_user["id"] != user_id and existing_user["email"] == update_data["email"]:
                raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    user.update(update_data)

    return public_user(user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    user = find_user(user_id)
    user_list.remove(user)

    return {"message": "회원 정보가 삭제되었습니다."}
