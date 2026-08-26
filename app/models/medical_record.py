from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class MedicalRecord(Base):
    """환자의 진료 기록(차트) 테이블"""

    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    chart_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="차트 번호"
    )
    symptoms: Mapped[str] = mapped_column(Text, nullable=False, comment="증상")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("current_timestamp(0)"),
        comment="진료 기록 등록 일시",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
        comment="진료 기록 수정 일시",
    )

    # 이 진료 기록이 속한 환자
    patient: Mapped["Patient"] = relationship(back_populates="medical_records")
    # 이 진료 기록에 업로드된 X-Ray 이미지들
    xray_images: Mapped[list["XrayImage"]] = relationship(
        back_populates="medical_record", cascade="all, delete-orphan"
    )
    # 이 진료 기록에 대한 AI 분석 결과들
    ai_analysis_results: Mapped[list["AIAnalysisResult"]] = relationship(
        back_populates="medical_record", cascade="all, delete-orphan"
    )
