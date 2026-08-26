from __future__ import annotations

from typing import Optional

from sqlalchemy import DateTime, Enum, BigInteger, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="환자 성명")
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="smallint")
    gender: Mapped[Optional[str]] = mapped_column(Enum("M", "F"), comment="환자 성별")
    phone: Mapped[str] = mapped_column(String(11), nullable=False, comment="환자 연락처, 국내 전화번호로 한정")
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("current_timestamp"), comment="환자 정보 등록 일시")
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True, onupdate=text("current_timestamp"), comment="환자 정보 수정 일시")

    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
