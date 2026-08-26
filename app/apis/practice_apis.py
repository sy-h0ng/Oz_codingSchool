import re

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

router = APIRouter(prefix="/practice_api", tags=["practice"])

# app/apis/practice_apis.py
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

# 이메일 형식 검사용 정규표현식
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# 비밀번호: 대문자 1개 이상 + 소문자 1개 이상 + 특수문자 1개 이상, 8~20자
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?\":{}|<>_\-+=~`\[\];'/\\]).{8,20}$"
)


class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str


class UserRegisterRequest(BaseModel):
    name: str
    age: int
    email: str
    password: str


class UserUpdateRequest(BaseModel):
    age: int | None = None
    email: str | None = None
    password: str | None = None


@router.get(
    "/users",
    summary="전체 회원 조회 API",
    response_model=list[UserResponse],
)
def get_all_user_handler():
    return user_list


@router.get(
    "/users/{user_id}",
    summary="단일 회원 조회 API",
    response_model=UserResponse,
)
def get_user_handler(
    user_id: int = Path(..., ge=1),
):
    for user in user_list:
        if user["id"] == user_id:
            return user
    # 클라이언트에게 요청 실패한 상황을 응답
    raise HTTPException(
        status_code=404,
        detail="유효한 id가 아닙니다.",
    )


@router.post(
    "/users",
    summary="회원 등록 API",
    status_code=201,  # 요청이 성공했을 때 사용되는 상태코드
    response_model=UserResponse,
)
def register_user_handler(
    body: UserRegisterRequest,
):
    # 이름 검증: 최소 2글자, 최대 10글자
    if not (2 <= len(body.name) <= 10):
        raise HTTPException(
            status_code=400,
            detail="이름은 최소 2글자, 최대 10글자여야 합니다.",
        )

    # 나이 검증: 최소 14세
    if body.age < 14:
        raise HTTPException(
            status_code=400,
            detail="나이는 최소 14세 이상이어야 합니다.",
        )

    # 이메일 검증: 정규표현식 + 최대 30자
    if len(body.email) > 30 or not EMAIL_PATTERN.match(body.email):
        raise HTTPException(
            status_code=400,
            detail="이메일 형식이 올바르지 않습니다.",
        )

    # 이메일 중복 검증
    for user in user_list:
        if user["email"] == body.email:
            raise HTTPException(
                status_code=400,
                detail="이미 사용 중인 이메일입니다.",
            )

    # 비밀번호 검증: 대소문자 + 특수문자 각 1개 이상, 8~20자
    if not PASSWORD_PATTERN.match(body.password):
        raise HTTPException(
            status_code=400,
            detail="비밀번호는 대소문자, 특수문자를 각 1개 이상 포함하여 최소 8자, 최대 20자여야 합니다.",
        )

    new_user = {
        # 기본키 생성 권한 -> 서버
        "id": len(user_list) + 1,  # 기본키 서버에서 발급 (1씩 자동 증가)
        "name": body.name,
        "age": body.age,
        "email": body.email,
        "password": body.password,
    }
    user_list.append(new_user)
    return new_user


@router.patch(
    "/users/{user_id}",
    summary="회원 정보 수정 API",
    response_model=UserResponse,
)
def update_user_handler(
    body: UserUpdateRequest,
    user_id: int = Path(..., ge=1),
):
    # 입력된 항목이 하나도 없으면 400
    if body.age is None and body.email is None and body.password is None:
        raise HTTPException(
            status_code=400,
            detail="수정할 항목을 최소 1개 이상 입력해주세요.",
        )

    for user in user_list:
        if user["id"] == user_id:
            if body.age is not None:
                if body.age < 14:
                    raise HTTPException(
                        status_code=400,
                        detail="나이는 최소 14세 이상이어야 합니다.",
                    )
                user["age"] = body.age

            if body.email is not None:
                if len(body.email) > 30 or not EMAIL_PATTERN.match(body.email):
                    raise HTTPException(
                        status_code=400,
                        detail="이메일 형식이 올바르지 않습니다.",
                    )
                user["email"] = body.email

            if body.password is not None:
                if not PASSWORD_PATTERN.match(body.password):
                    raise HTTPException(
                        status_code=400,
                        detail="비밀번호는 대소문자, 특수문자를 각 1개 이상 포함하여 최소 8자, 최대 20자여야 합니다.",
                    )
                user["password"] = body.password

            return user

    raise HTTPException(
        status_code=404,
        detail="유효한 id가 아닙니다.",
    )


@router.delete(
    "/users/{user_id}",
    summary="회원 삭제 API",
)
def delete_user_handler(
    user_id: int = Path(..., ge=1),
):
    for user in user_list:
        if user["id"] == user_id:
            user_list.remove(user)
            return {"detail": f"id {user_id} 회원이 삭제되었습니다."}

    raise HTTPException(
        status_code=404,
        detail="유효한 id가 아닙니다.",
    )
