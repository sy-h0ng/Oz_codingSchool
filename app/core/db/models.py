import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7


class UUIDMixin:
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        CHAR(36), primary_key=True, default=uuid7
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), server_default=text("current_timestamp(0)")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc), server_default=text("current_timestamp(0)")
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
