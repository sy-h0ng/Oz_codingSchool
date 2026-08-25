from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
import re



router = APIRouter(prefix="/practice_api", tags=["practice"])

user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!"
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!"
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@"
    }
]

@router.get("/users")
def get_users():
    return [
        {"id": u["id"], "name": u["name"], "age": u["age"], "email": u["email"]}
        for u in user_list
    ]


@router.get("/users/{user_id}")
def get_user(user_id: int):
    for u in user_list:
        if u["id"] == user_id:
            return {"id": u["id"], "name": u["name"], "age": u["age"], "email": u["email"]}
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    age: int = Field(ge=14)
    email: str = Field(max_length=30)
    password: str = Field(min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        if any(u["email"] == v for u in user_list):
            raise ValueError("이미 사용 중인 이메일입니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v) or not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("비밀번호는 대소문자, 특수문자를 각 1개 이상 포함해야 합니다.")
        return v    

@router.post("/users")
def create_user(user: UserCreate):
    new_id = max([u["id"] for u in user_list], default=0) + 1
    new_user = {"id": new_id, **user.model_dump()}
    user_list.append(new_user)
    return {"id": new_user["id"], "name": new_user["name"], "age": new_user["age"], "email": new_user["email"]}



class UserUpdate(BaseModel):
    age: int | None = Field(default=None, ge=14)
    email: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is None:
            return v
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if v is None:
            return v
        if not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v) or not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("비밀번호는 대소문자, 특수문자를 각 1개 이상 포함해야 합니다.")
        return v


@router.patch("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate):
    if user_update.age is None and user_update.email is None and user_update.password is None:
        raise HTTPException(status_code=400, detail="수정할 항목을 최소 하나 이상 입력해야 합니다.")

    for u in user_list:
        if u["id"] == user_id:
            if user_update.age is not None:
                u["age"] = user_update.age
            if user_update.email is not None:
                u["email"] = user_update.email
            if user_update.password is not None:
                u["password"] = user_update.password
            return {"id": u["id"], "name": u["name"], "age": u["age"], "email": u["email"]}

    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    for i, u in enumerate(user_list):
        if u["id"] == user_id:
            user_list.pop(i)
            return
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")