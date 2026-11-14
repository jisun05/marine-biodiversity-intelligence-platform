from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DataCollection(Base):
    __tablename__ = "data_collections"

    id: Mapped[int] = mapped_column(primary_key=True)

    scientific_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sources: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    total_fetched: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_inserted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    total_transformed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
