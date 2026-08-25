# app/apis/practice_apis.py

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import re

router = APIRouter(prefix="/practice_api/users", tags=["Practice Users"])

# 초기 데이터
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

# 정규식 패턴
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
# 대문자, 소문자, 특수문자 각 1개 이상 포함, 8~20자
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,20}$"


# 1. 응답용 스키마 (비밀번호 제외)
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str


# 2. 회원 등록 요청 스키마
class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=10)
    age: int = Field(..., ge=14)
    email: str = Field(..., max_length=30)
    password: str

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "비밀번호는 대소문자 및 특수문자를 각 1개 이상 포함하여 8~20자여야 합니다."
            )
        return v


# 3. 회원 수정 요청 스키마
class UserUpdateRequest(BaseModel):
    age: Optional[int] = Field(None, ge=14)
    email: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = None

    @field_validator("email")
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(EMAIL_REGEX, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v

    @field_validator("password")
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "비밀번호는 대소문자 및 특수문자를 각 1개 이상 포함하여 8~20자여야 합니다."
            )
        return v


# API 1: 모든 회원 목록 조회
@router.get("", response_model=List[UserResponse])
def get_all_users():
    return user_list


# API 2: 특정 회원 단일 조회
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int):
    for user in user_list:
        if user["id"] == user_id:
            return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="해당 ID의 회원을 찾을 수 없습니다.",
    )


# API 3: 회원 등록
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreateRequest):
    # 이메일 중복 검사
    if any(user["email"] == user_data.email for user in user_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다.",
        )

    # 신규 ID 계산 (자동 증가)
    new_id = max([user["id"] for user in user_list], default=0) + 1

    new_user = {
        "id": new_id,
        "name": user_data.name,
        "age": user_data.age,
        "email": user_data.email,
        "password": user_data.password,
    }
    user_list.append(new_user)
    return new_user


# API 4: 회원 정보 수정
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdateRequest):
    # 입력된 필드 추출 (None 제외)
    update_fields = user_data.model_dump(exclude_unset=True)

    # 모든 항목이 입력되지 않은 경우 400 에러
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목이 최소 1개 이상 입력되어야 합니다.",
        )

    # 대상 유저 검색
    target_user = next((u for u in user_list if u["id"] == user_id), None)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 ID의 회원을 찾을 수 없습니다.",
        )

    # 입력된 항목만 수정 반영
    for key, value in update_fields.items():
        target_user[key] = value

    return target_user


# API 5: 회원 정보 삭제
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    target_user = next((u for u in user_list if u["id"] == user_id), None)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 ID의 회원을 찾을 수 없습니다.",
        )

    user_list.remove(target_user)
    return None
