from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class XrayImage(Base):
    """진료 기록에 첨부된 X-Ray 이미지 테이블"""

    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False
    )
    # NOTE: users.id가 integer PK이므로 FK 타입을 맞추기 위해 Integer로 선언합니다.
    #       (ERD 상에는 bigint로 표기되어 있으나, users.id와 타입을 맞추지 않으면
    #        MySQL에서 FK 제약조건 생성이 실패합니다.)
    uploader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(
        String(2048), nullable=False, comment="업로드된 X-Ray 이미지 URL"
    )
    shooting_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="X-Ray 촬영 일시"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("current_timestamp(0)"),
        comment="이미지 등록(업로드) 일시",
    )

    # 이 이미지가 속한 진료 기록
    medical_record: Mapped["MedicalRecord"] = relationship(back_populates="xray_images")
    # 이 이미지를 업로드한 유저
    uploader: Mapped["User"] = relationship(back_populates="uploaded_xray_images")
