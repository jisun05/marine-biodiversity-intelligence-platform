from datetime import date

from pydantic import BaseModel, ConfigDict


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_record_id: str

    scientific_name: str
    taxon_id: str | None

    basis_of_record: str | None
    event_date: date | None

    latitude: float | None
    longitude: float | None

    coordinate_uncertainty_m: float | None
    country_code: str | None

    dataset_id: str | None


class ObservationListResponse(BaseModel):
    total: int
    items: list[ObservationResponse]