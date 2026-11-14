from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models import Observation, ObservationTaxonomy, Taxon
from backend.app.schemas.observation_schemas import (
    ObservationListResponse,
)
from backend.app.schemas.taxonomy_schemas import TaxonListResponse


router = APIRouter(
    prefix="/taxa",
    tags=["Taxonomy"],
)


@router.get("", response_model=TaxonListResponse)
def get_taxa(
    search: str | None = Query(
        default=None,
        min_length=1,
        description="Search by canonical scientific name",
    ),
    rank: str | None = Query(
        default=None,
        min_length=1,
        description="Filter by taxonomic rank",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve marine taxa with observation counts.
    """

    query = (
        select(
            Taxon,
            func.count(ObservationTaxonomy.observation_id).label(
                "observation_count"
            ),
        )
        .outerjoin(
            ObservationTaxonomy,
            Taxon.aphia_id == ObservationTaxonomy.aphia_id,
        )
        .group_by(Taxon.aphia_id)
    )

    if search:
        query = query.where(
            Taxon.canonical_name.ilike(f"%{search}%")
        )

    if rank:
        query = query.where(
            Taxon.taxonomic_rank.ilike(rank)
        )

    count_query = select(func.count()).select_from(
        query.subquery()
    )

    total = db.scalar(count_query)

    query = (
        query
        .order_by(Taxon.canonical_name)
        .offset(skip)
        .limit(limit)
    )

    results = db.execute(query).all()

    items = [
        {
            "aphia_id": taxon.aphia_id,
            "canonical_name": taxon.canonical_name,
            "authority": taxon.authority,
            "taxonomic_rank": taxon.taxonomic_rank,
            "parent_aphia_id": taxon.parent_aphia_id,
            "observation_count": observation_count,
        }
        for taxon, observation_count in results
    ]

    return {
        "total": total,
        "items": items,
    }


@router.get(
    "/{aphia_id}/observations",
    response_model=ObservationListResponse,
)
def get_taxon_observations(
    aphia_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve observations associated with a WoRMS taxon.
    """

    taxon = db.get(Taxon, aphia_id)

    if taxon is None:
        raise HTTPException(
            status_code=404,
            detail=f"Taxon with AphiaID {aphia_id} not found.",
        )

    query = (
        select(Observation)
        .join(
            ObservationTaxonomy,
            Observation.id == ObservationTaxonomy.observation_id,
        )
        .where(ObservationTaxonomy.aphia_id == aphia_id)
    )

    count_query = (
        select(func.count())
        .select_from(Observation)
        .join(
            ObservationTaxonomy,
            Observation.id == ObservationTaxonomy.observation_id,
        )
        .where(ObservationTaxonomy.aphia_id == aphia_id)
    )

    total = db.scalar(count_query)

    query = (
        query
        .order_by(Observation.id)
        .offset(skip)
        .limit(limit)
    )

    observations = db.scalars(query).all()

    return {
        "total": total,
        "items": observations,
    }
