from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy import BigInteger as SABigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class AIAnalysisResult(Base):
    """진료 기록(X-Ray)에 대한 AI 폐렴 예측 분석 결과 테이블"""

    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(SABigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        SABigInteger, ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False
    )
    is_pneumonia: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="AI 모델의 폐렴 여부 예측 결과"
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, comment="예측 신뢰도(확률, %)"
    )
    heatmap_url: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="AI가 근거로 삼은 부위를 표시한 히트맵 이미지 URL"
    )
    ai_model: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="분석에 사용된 AI 모델명/버전"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("current_timestamp(0)"),
        comment="분석 결과 생성 일시",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
        comment="분석 결과 수정 일시",
    )

    # 이 분석 결과가 속한 진료 기록
    medical_record: Mapped["MedicalRecord"] = relationship(
        back_populates="ai_analysis_results"
    )
