from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.observation import Observation
from backend.app.schemas.observation_schemas import (
    ObservationListResponse,
)


router = APIRouter(
    prefix="/observations",
    tags=["Observations"],
)

@router.get("/statistics")
def get_observation_statistics(
    db: Session = Depends(get_db),
):
    """
    Retrieve global observation counts by data source.
    """

    count_query = (
        select(
            Observation.source,
            func.count(Observation.id).label("count"),
        )
        .group_by(Observation.source)
    )

    results = db.execute(count_query).all()

    counts = {
        "GBIF": 0,
        "OBIS": 0,
    }

    for source, count in results:
        if source in counts:
            counts[source] = count

    return {
        "total_observations": sum(counts.values()),
        "gbif_records": counts["GBIF"],
        "obis_records": counts["OBIS"],
    }


@router.get("", response_model=ObservationListResponse)
def get_observations(
    source: str | None = Query(
    default=None,
    pattern="(?i)^(GBIF|OBIS)$",
    description="Filter by data source (GBIF or OBIS)",
    ),
    scientific_name: str | None = Query(
        default=None,
        min_length=1,
        description="Search by scientific name",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve biodiversity observations with optional filters.
    """

    query = select(Observation)

    # Filter by data source
    if source:
        query = query.where(
            Observation.source == source.upper()
        )

    # Search by scientific name
    if scientific_name:
        query = query.where(
            Observation.scientific_name.ilike(
                f"%{scientific_name}%"
            )
        )

    # Count matching records
    count_query = select(func.count()).select_from(
        query.subquery()
    )

    total = db.scalar(count_query)

    # Apply pagination
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