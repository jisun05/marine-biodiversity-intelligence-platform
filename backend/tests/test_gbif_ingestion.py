from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from backend.app.models.gbif_raw_observation import GBIFRawObservation
from backend.app.services import gbif_ingestion


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_ingest_gbif_new_records(db_session, monkeypatch):
    records = [
        {
            "gbifID": "100001",
            "scientificName": "Balaenoptera musculus",
            "decimalLatitude": 35.0,
            "decimalLongitude": 129.0,
        },
        {
            "gbifID": "100002",
            "scientificName": "Balaenoptera musculus",
            "decimalLatitude": 36.0,
            "decimalLongitude": 130.0,
        },
    ]

    monkeypatch.setattr(
        gbif_ingestion,
        "fetch_gbif_occurrences",
        AsyncMock(return_value={"results": records}),
    )

    result = await gbif_ingestion.ingest_gbif_occurrences(
        db=db_session,
        scientific_name="Balaenoptera musculus",
        limit=10,
    )

    assert result == {
        "fetched": 2,
        "inserted": 2,
        "skipped": 0,
    }

    stored_records = db_session.scalars(
        select(GBIFRawObservation)
    ).all()

    assert len(stored_records) == 2


@pytest.mark.anyio
async def test_ingest_gbif_skips_existing_records(
    db_session,
    monkeypatch,
):
    existing_record = GBIFRawObservation(
        source_record_id="100001",
        raw_data={
            "gbifID": "100001",
            "scientificName": "Balaenoptera musculus",
        },
    )

    db_session.add(existing_record)
    db_session.commit()

    records = [
        {
            "gbifID": "100001",
            "scientificName": "Balaenoptera musculus",
        },
        {
            "gbifID": "100002",
            "scientificName": "Balaenoptera musculus",
        },
    ]

    monkeypatch.setattr(
        gbif_ingestion,
        "fetch_gbif_occurrences",
        AsyncMock(return_value={"results": records}),
    )

    result = await gbif_ingestion.ingest_gbif_occurrences(
        db=db_session,
        scientific_name="Balaenoptera musculus",
        limit=10,
    )

    assert result == {
        "fetched": 2,
        "inserted": 1,
        "skipped": 1,
    }

    stored_records = db_session.scalars(
        select(GBIFRawObservation)
    ).all()

    assert len(stored_records) == 2


@pytest.mark.anyio
async def test_ingest_gbif_empty_response(db_session, monkeypatch):
    monkeypatch.setattr(
        gbif_ingestion,
        "fetch_gbif_occurrences",
        AsyncMock(return_value={"results": []}),
    )

    result = await gbif_ingestion.ingest_gbif_occurrences(
        db=db_session,
        scientific_name="Balaenoptera musculus",
        limit=10,
    )

    assert result == {
        "fetched": 0,
        "inserted": 0,
        "skipped": 0,
    }

    stored_records = db_session.scalars(
        select(GBIFRawObservation)
    ).all()

    assert len(stored_records) == 0

@pytest.mark.anyio
async def test_ingest_gbif_rolls_back_on_database_error(
    db_session,
    monkeypatch,
    ):

    records = [
        {
            "gbifID": "100003",
            "scientificName": "Balaenoptera musculus",
        }
    ]

    monkeypatch.setattr(
        gbif_ingestion,
        "fetch_gbif_occurrences",
        AsyncMock(return_value={"results": records}),
    )

    monkeypatch.setattr(
        db_session,
        "execute",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(Exception("Database error")),
    )

    with pytest.raises(Exception, match="Database error"):
        await gbif_ingestion.ingest_gbif_occurrences(
            db=db_session,
            scientific_name="Balaenoptera musculus",
            limit=10,
        )

    stored_record = db_session.scalar(
        select(GBIFRawObservation).where(
            GBIFRawObservation.source_record_id == "100003"
        )
    )

    assert stored_record is None

@pytest.mark.anyio
async def test_ingest_gbif_large_batch(db_session, monkeypatch):
    records = [
        {
            "gbifID": str(300000 + i),
            "scientificName": "Balaenoptera musculus",
            "decimalLatitude": 35.0,
            "decimalLongitude": 129.0,
        }
        for i in range(750)
    ]

    monkeypatch.setattr(
        gbif_ingestion,
        "fetch_gbif_occurrences",
        AsyncMock(return_value={
            "count": 10000,
            "results": records,
        }),
    )

    result = await gbif_ingestion.ingest_gbif_occurrences(
        db=db_session,
        scientific_name="Balaenoptera musculus",
        limit=750,
    )

    assert result == {
        "fetched": 750,
        "inserted": 750,
        "skipped": 0,
    }

    stored_records = db_session.scalars(
        select(GBIFRawObservation)
    ).all()

    assert len(stored_records) == 750
