"""create ai health tables

Revision ID: 20260826_143000
Revises:
Create Date: 2026-08-26 14:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260826_143000"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True, comment="평문 저장 x -> 해쉬화 된 비밀번호 저장"),
        sa.Column("name", sa.String(length=20), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True, comment="유저 휴대폰 번호"),
        sa.Column("gender", sa.Enum("M", "F"), nullable=False, comment="성별 선택"),
        sa.Column("department", sa.Enum("MEDICAL", "DEV", "RESEARCH"), nullable=False, comment="부서 선택"),
        sa.Column("role", sa.Enum("PENDING", "STAFF", "ADMIN"), nullable=False, comment="부여된 역할 권한"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False, comment="계정 활성화 여부"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp"), nullable=False, comment="유저 생성 일시"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="유저 정보 수정 일시"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_table(
        "patients",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=30), nullable=False, comment="환자 성명"),
        sa.Column("age", sa.SmallInteger(), nullable=False, comment="smallint"),
        sa.Column("gender", sa.Enum("M", "F"), nullable=True, comment="환자 성별"),
        sa.Column("phone", sa.String(length=11), nullable=False, comment="환자 연락처, 국내 전화번호로 한정"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp"), nullable=False, comment="환자 정보 등록 일시"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="환자 정보 수정 일시"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "medical_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False, comment="환자 정보 테이블 FK"),
        sa.Column("chart_number", sa.String(length=50), nullable=False, comment="환자 진료 차트 번호"),
        sa.Column("symptoms", sa.Text(), nullable=False, comment="환자 증상 기록"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp"), nullable=False, comment="진료 정보 등록 일시"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="진료 정보 수정 일시"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chart_number"),
    )
    op.create_table(
        "xray_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.BigInteger(), nullable=False, comment="진료 기록 id"),
        sa.Column("uploader_id", sa.Integer(), nullable=True, comment="X-ray 이미지를 업로드한 유저의 id"),
        sa.Column("image_url", sa.String(length=2048), nullable=False, comment="이미지 url"),
        sa.Column("shooting_datetime", sa.DateTime(), nullable=False, comment="X-ray 촬영일시"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp"), nullable=False, comment="X-ray 이미지 등록 일시"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_analysis_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.BigInteger(), nullable=False, comment="진료 기록 id"),
        sa.Column("is_pneumonia", sa.Boolean(), nullable=False, comment="폐렴 진단 여부"),
        sa.Column("confidence", sa.DECIMAL(precision=5, scale=2), nullable=False, comment="AI 예측 신뢰도"),
        sa.Column("heatmap_url", sa.String(length=255), nullable=False, comment="AI가 판별한 병변 표시 이미지 url"),
        sa.Column("ai_model", sa.String(length=50), nullable=False, comment="AI 예측에 사용된 모델명 혹은 모델파일"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp"), nullable=False, comment="AI 폐렴 예측 결과 생성일시"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, comment="수정 일시"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ai_analysis_results")
    op.drop_table("xray_images")
    op.drop_table("medical_records")
    op.drop_table("patients")
    op.drop_table("users")
