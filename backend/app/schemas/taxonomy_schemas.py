from pydantic import BaseModel, ConfigDict


class TaxonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aphia_id: int
    canonical_name: str
    authority: str | None
    taxonomic_rank: str
    parent_aphia_id: int | None

    observation_count: int


class TaxonListResponse(BaseModel):
    total: int
    items: list[TaxonResponse]
