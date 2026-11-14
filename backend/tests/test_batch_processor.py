import pytest
from unittest.mock import AsyncMock

from backend.app.models.data_collection import DataCollection
from backend.app.services import batch_processor


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_process_batch_success(db_session, monkeypatch):
    mock_collect = AsyncMock(
        side_effect=[
            {
                "scientific_name": "Megaptera novaeangliae",
                "status": "completed",
                "total_fetched": 20,
                "total_inserted": 18,
                "total_transformed": 18,
                "successful_sources": ["GBIF", "OBIS"],
                "failed_sources": [],
            },
            {
                "scientific_name": "Carcharodon carcharias",
                "status": "completed",
                "total_fetched": 15,
                "total_inserted": 12,
                "total_transformed": 12,
                "successful_sources": ["GBIF", "OBIS"],
                "failed_sources": [],
            },
        ]
    )

    monkeypatch.setattr(
        batch_processor,
        "collect_species_data",
        mock_collect,
    )

    results = await batch_processor.process_batch(
        db=db_session,
        scientific_names=[
            "Megaptera novaeangliae",
            "Carcharodon carcharias",
        ],
        sources=["GBIF", "OBIS"],
        limit=10,
    )

    assert len(results) == 2

    assert results[0].status == "completed"
    assert results[0].total_fetched == 20
    assert results[0].total_transformed == 18

    assert results[1].status == "completed"
    assert results[1].total_fetched == 15
    assert results[1].total_transformed == 12

    assert mock_collect.await_count == 2


@pytest.mark.anyio
async def test_process_batch_continues_after_failure(db_session, monkeypatch):
    mock_collect = AsyncMock(
        side_effect=[
            RuntimeError("GBIF API unavailable"),
            {
                "scientific_name": "Carcharodon carcharias",
                "status": "completed",
                "total_fetched": 10,
                "total_inserted": 8,
                "total_transformed": 8,
                "successful_sources": ["GBIF", "OBIS"],
                "failed_sources": [],
            },
        ]
    )

    monkeypatch.setattr(
        batch_processor,
        "collect_species_data",
        mock_collect,
    )

    results = await batch_processor.process_batch(
        db=db_session,
        scientific_names=[
            "Megaptera novaeangliae",
            "Carcharodon carcharias",
        ],
        sources=["GBIF", "OBIS"],
        limit=10,
    )

    assert len(results) == 2

    assert results[0].status == "failed"
    assert "GBIF API unavailable" in results[0].error_message

    assert results[1].status == "completed"
    assert results[1].total_transformed == 8

    assert mock_collect.await_count == 2