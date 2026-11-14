from typing import Any
from sqlalchemy.orm import Session

from backend.app.models import ObservationTaxonomy, Taxon


def persist_taxonomy_mapping(
    db: Session,
    observation_id: int,
    resolved_taxon: dict[str, Any],
) -> ObservationTaxonomy:
    """
    Persist a resolved WoRMS taxon and link it to an observation.

    The caller is responsible for committing or rolling back
    the transaction.
    """

    required_fields = (
        "aphia_id",
        "canonical_name",
        "taxonomic_rank",
    )

    missing_fields = [
        field
        for field in required_fields
        if not resolved_taxon.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required taxonomy fields: {missing_fields}"
        )

    aphia_id = int(resolved_taxon["aphia_id"])

    # Find an existing taxon by its WoRMS AphiaID.
    taxon = db.get(Taxon, aphia_id)

    if taxon is None:
        taxon = Taxon(
            aphia_id=aphia_id,
            canonical_name=resolved_taxon["canonical_name"],
            authority=resolved_taxon.get("authority"),
            taxonomic_rank=resolved_taxon["taxonomic_rank"],
            parent_aphia_id=resolved_taxon.get("parent_aphia_id"),
        )
        db.add(taxon)
    else:
        # Refresh existing taxonomy information.
        taxon.canonical_name = resolved_taxon["canonical_name"]
        taxon.authority = resolved_taxon.get("authority")
        taxon.taxonomic_rank = resolved_taxon["taxonomic_rank"]
        taxon.parent_aphia_id = resolved_taxon.get("parent_aphia_id")

    db.flush()

    # Find an existing observation-taxonomy mapping.
    mapping = db.get(ObservationTaxonomy, observation_id)

    if mapping is None:
        mapping = ObservationTaxonomy(
            observation_id=observation_id,
            aphia_id=aphia_id,
            taxonomy_source="WORMS",
            match_type=resolved_taxon.get("match_type"),
            original_status=resolved_taxon.get("original_status"),
        )
        db.add(mapping)
    else:
        mapping.aphia_id = aphia_id
        mapping.taxonomy_source = "WORMS"
        mapping.match_type = resolved_taxon.get("match_type")
        mapping.original_status = resolved_taxon.get("original_status")

    db.flush()

    return mapping
