from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.models.enums import DepartmentEnum, GenderEnum, RoleEnum


class User(Base):
    """오즈코딩스쿨 AI 헬스케어 서비스의 내부 사용자(개발팀/의료진/연구진) 테이블"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="평문 저장 X -> 해시화 된 비밀번호 저장"
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, comment="유저 휴대폰 번호"
    )
    gender: Mapped[GenderEnum] = mapped_column(
        SAEnum(GenderEnum, native_enum=False, length=10, validate_strings=True),
        nullable=False,
        comment="성별 선택",
    )
    department: Mapped[DepartmentEnum] = mapped_column(
        SAEnum(DepartmentEnum, native_enum=False, length=20, validate_strings=True),
        nullable=False,
        comment="부서 선택",
    )
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, native_enum=False, length=20, validate_strings=True),
        nullable=False,
        comment="부여된 역할 권한",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), comment="계정 활성화 여부"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("current_timestamp(0)"),
        comment="유저 생성 일시",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
        comment="유저 정보 수정 일시",
    )

    # 이 유저가 업로드한 X-Ray 이미지들
    uploaded_xray_images: Mapped[list["XrayImage"]] = relationship(
        back_populates="uploader"
    )
