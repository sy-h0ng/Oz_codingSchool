from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, DECIMAL, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class AiAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="진료 기록 id",
    )
    is_pneumonia: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="폐렴 진단 여부")
    confidence: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False, comment="AI 예측 신뢰도")
    heatmap_url: Mapped[str] = mapped_column(String(255), nullable=False, comment="AI가 판별한 병변 표시 이미지 url")
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False, comment="AI 예측에 사용된 모델명 혹은 모델파일")
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("current_timestamp"), comment="AI 폐렴 예측 결과 생성일시")
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True, onupdate=text("current_timestamp"), comment="수정 일시")

    medical_record = relationship("MedicalRecord", back_populates="ai_analysis_results")
