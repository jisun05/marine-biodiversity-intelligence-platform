from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class GBIFRawObservation(Base):
    __tablename__ = "gbif_raw_observations"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_record_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    raw_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )