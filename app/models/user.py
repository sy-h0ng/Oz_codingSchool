from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), comment="평문 저장 x -> 해쉬화 된 비밀번호 저장")
    name: Mapped[Optional[str]] = mapped_column(String(20))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment="유저 휴대폰 번호")
    gender: Mapped[str] = mapped_column(Enum("M", "F"), nullable=False, comment="성별 선택")
    department: Mapped[str] = mapped_column(Enum("MEDICAL", "DEV", "RESEARCH"), nullable=False, comment="부서 선택")
    role: Mapped[str] = mapped_column(Enum("PENDING", "STAFF", "ADMIN"), nullable=False, comment="부여된 역할 권한")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), comment="계정 활성화 여부")
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("current_timestamp"), comment="유저 생성 일시")
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True, onupdate=text("current_timestamp"), comment="유저 정보 수정 일시")

    xray_images = relationship("XrayImage", back_populates="uploader")
