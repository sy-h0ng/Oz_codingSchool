from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, SmallInteger, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.models.enums import GenderEnum


class Patient(Base):
    """진료 대상이 되는 환자 정보 테이블"""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="환자 성명")
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="환자 나이")
    gender: Mapped[Optional[GenderEnum]] = mapped_column(
        SAEnum(GenderEnum, native_enum=False, length=10, validate_strings=True),
        nullable=True,
        comment="환자 성별",
    )
    phone: Mapped[str] = mapped_column(
        String(11), nullable=False, comment="환자 연락처, 국내 전화번호로 한정"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("current_timestamp(0)"),
        comment="환자 등록 일시",
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
        comment="환자 정보 수정 일시",
    )

    # 이 환자의 진료 기록들
    medical_records: Mapped[List["MedicalRecord"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
