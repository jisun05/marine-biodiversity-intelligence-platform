from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DataCollectionCreate(BaseModel):
    scientific_names: list[str] = Field(
        min_length=1,
        description="Scientific names of species to collect",
    )

    sources: list[Literal["GBIF", "OBIS"]] = Field(
        default=["GBIF", "OBIS"],
        min_length=1,
        description="Data sources to collect from",
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Maximum number of records per species and source",
    )


class DataCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scientific_name: str
    sources: list[str]
    trigger_type: str
    status: str
    total_fetched: int
    total_inserted: int
    total_transformed: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class DataCollectionListResponse(BaseModel):
    total: int
    items: list[DataCollectionResponse]
