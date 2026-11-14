from datetime import date

from sqlalchemy import Date, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Observation(Base):
    __tablename__ = "observations"

    __table_args__ = (
        UniqueConstraint("source", "source_record_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)

    scientific_name: Mapped[str] = mapped_column(String(255), nullable=False)
    taxon_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    basis_of_record: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    coordinate_uncertainty_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(255), nullable=True)

    dataset_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
