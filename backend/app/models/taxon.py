from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Taxon(Base):
    __tablename__ = "taxa"

    # WoRMS AphiaID
    aphia_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Accepted scientific name
    canonical_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    authority: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Species, Subspecies, Genus, etc.
    taxonomic_rank: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # WoRMS parent AphiaID
    parent_aphia_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )