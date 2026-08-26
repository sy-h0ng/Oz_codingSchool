from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class XrayImage(Base):
    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="진료 기록 id",
    )
    uploader_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="X-ray 이미지를 업로드한 유저의 id",
    )
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False, comment="이미지 url")
    shooting_datetime: Mapped[str] = mapped_column(DateTime, nullable=False, comment="X-ray 촬영일시")
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("current_timestamp"), comment="X-ray 이미지 등록 일시")

    medical_record = relationship("MedicalRecord", back_populates="xray_images")
    uploader = relationship("User", back_populates="xray_images")
