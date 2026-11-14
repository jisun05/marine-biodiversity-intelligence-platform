from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.data_collection import DataCollection
from backend.app.schemas.data_collection_schemas import (
    DataCollectionCreate,
    DataCollectionListResponse,
    DataCollectionResponse,
)
from backend.app.services.batch_processor import process_batch


router = APIRouter(
    prefix="/data-collections",
    tags=["Data Collections"],
)


@router.post("", response_model=DataCollectionListResponse)
async def create_data_collections(
    request: DataCollectionCreate,
    db: Session = Depends(get_db),
):
    """
    Start batch collection for multiple marine species.
    """

    collections = await process_batch(
        db=db,
        scientific_names=request.scientific_names,
        sources=request.sources,
        limit=request.limit,
    )

    return {
        "total": len(collections),
        "items": collections,
    }


@router.get("", response_model=DataCollectionListResponse)
def get_data_collections(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve data collection jobs with pagination.
    """

    count_query = select(func.count()).select_from(DataCollection)
    total = db.scalar(count_query)

    query = (
        select(DataCollection)
        .order_by(DataCollection.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    collections = db.scalars(query).all()

    return {
        "total": total,
        "items": collections,
    }


@router.get(
    "/{collection_id}",
    response_model=DataCollectionResponse,
)
def get_data_collection(
    collection_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific data collection job.
    """

    collection = db.get(DataCollection, collection_id)

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Data collection not found",
        )

    return collection