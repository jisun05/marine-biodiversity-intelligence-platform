from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ObservationTaxonomy(Base):
    __tablename__ = "observation_taxonomy"

    # One taxonomy mapping per observation
    observation_id: Mapped[int] = mapped_column(
        ForeignKey("observations.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # WoRMS accepted AphiaID
    aphia_id: Mapped[int] = mapped_column(
        ForeignKey("taxa.aphia_id"),
        nullable=False,
        index=True,
    )

    taxonomy_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="WORMS",
    )

    # Exact, fuzzy, etc.
    match_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Status of the original taxonomic record
    original_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )