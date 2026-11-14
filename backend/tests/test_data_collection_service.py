from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services import data_collection_service


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_collect_species_data_success(monkeypatch):
    db = MagicMock()

    async def mock_ingestion(**kwargs):
        return {
            "fetched": 10,
            "inserted": 8,
            "skipped": 2,
        }

    def mock_transformer(**kwargs):
        return {
            "fetched": 10,
            "inserted": 8,
            "skipped": 2,
        }

    monkeypatch.setattr(
        data_collection_service,
        "ingest_gbif_occurrences",
        AsyncMock(side_effect=mock_ingestion),
    )

    monkeypatch.setattr(
        data_collection_service,
        "transform_gbif_observations",
        mock_transformer,
    )

    monkeypatch.setattr(
        data_collection_service,
        "ingest_obis_occurrences",
        AsyncMock(side_effect=mock_ingestion),
    )

    monkeypatch.setattr(
        data_collection_service,
        "transform_obis_observations",
        mock_transformer,
    )

    result = await data_collection_service.collect_species_data(
        db=db,
        scientific_name="Balaenoptera musculus",
        sources=["GBIF", "OBIS"],
        limit=10,
    )

    assert result["status"] == "completed"
    assert result["total_fetched"] == 20
    assert result["total_inserted"] == 16
    assert result["total_transformed"] == 16
    assert result["successful_sources"] == ["GBIF", "OBIS"]
    assert result["failed_sources"] == []


@pytest.mark.anyio
async def test_collection_continues_when_one_source_fails(monkeypatch):
    db = MagicMock()

    async def mock_gbif_failure(**kwargs):
        raise Exception("GBIF API unavailable")

    async def mock_obis_success(**kwargs):
        return {
            "fetched": 10,
            "inserted": 8,
            "skipped": 2,
        }

    def mock_obis_transformer(**kwargs):
        return {
            "fetched": 10,
            "inserted": 8,
            "skipped": 2,
        }

    monkeypatch.setattr(
        data_collection_service,
        "ingest_gbif_occurrences",
        AsyncMock(side_effect=mock_gbif_failure),
    )

    monkeypatch.setattr(
        data_collection_service,
        "ingest_obis_occurrences",
        AsyncMock(side_effect=mock_obis_success),
    )

    monkeypatch.setattr(
        data_collection_service,
        "transform_obis_observations",
        mock_obis_transformer,
    )

    result = await data_collection_service.collect_species_data(
        db=db,
        scientific_name="Balaenoptera musculus",
        sources=["GBIF", "OBIS"],
        limit=10,
    )

    assert result["status"] == "partial"
    assert result["successful_sources"] == ["OBIS"]
    assert len(result["failed_sources"]) == 1
    assert result["failed_sources"][0]["source"] == "GBIF"
    assert result["total_fetched"] == 10
    assert result["total_transformed"] == 8

    db.rollback.assert_called_once()