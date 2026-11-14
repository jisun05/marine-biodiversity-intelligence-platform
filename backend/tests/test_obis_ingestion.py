from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from backend.app.models.obis_raw_observation import OBISRawObservation
from backend.app.services import obis_ingestion


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_ingest_obis_new_records(db_session, monkeypatch):
    records = [
        {
            "id": "200001",
            "scientificName": "Balaenoptera musculus",
            "decimalLatitude": 35.0,
            "decimalLongitude": 129.0,
        },
        {
            "id": "200002",
            "scientificName": "Balaenoptera musculus",
            "decimalLatitude": 36.0,
            "decimalLongitude": 130.0,
        },
    ]

    monkeypatch.setattr(
        obis_ingestion,
        "fetch_obis_occurrences",
        AsyncMock(return_value={"results": records}),
    )

    result = await obis_ingestion.ingest_obis_occurrences(
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
        select(OBISRawObservation)
    ).all()

    assert len(stored_records) == 2


@pytest.mark.anyio
async def test_ingest_obis_skips_existing_records(
    db_session,
    monkeypatch,
):
    existing_record = OBISRawObservation(
        source_record_id="200001",
        raw_data={
            "id": "200001",
            "scientificName": "Balaenoptera musculus",
        },
    )

    db_session.add(existing_record)
    db_session.commit()

    records = [
        {
            "id": "200001",
            "scientificName": "Balaenoptera musculus",
        },
        {
            "id": "200002",
            "scientificName": "Balaenoptera musculus",
        },
    ]

    monkeypatch.setattr(
        obis_ingestion,
        "fetch_obis_occurrences",
        AsyncMock(return_value={"results": records}),
    )

    result = await obis_ingestion.ingest_obis_occurrences(
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
        select(OBISRawObservation)
    ).all()

    assert len(stored_records) == 2


@pytest.mark.anyio
async def test_ingest_obis_empty_response(db_session, monkeypatch):
    monkeypatch.setattr(
        obis_ingestion,
        "fetch_obis_occurrences",
        AsyncMock(return_value={"results": []}),
    )

    result = await obis_ingestion.ingest_obis_occurrences(
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
        select(OBISRawObservation)
    ).all()

    assert len(stored_records) == 0


@pytest.mark.anyio
async def test_ingest_obis_rolls_back_on_database_error(
    db_session,
    monkeypatch,
):
    records = [
        {
            "id": "200003",
            "scientificName": "Balaenoptera musculus",
        }
    ]

    monkeypatch.setattr(
        obis_ingestion,
        "fetch_obis_occurrences",
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
        await obis_ingestion.ingest_obis_occurrences(
            db=db_session,
            scientific_name="Balaenoptera musculus",
            limit=10,
        )

    monkeypatch.undo()

    stored_record = db_session.scalar(
        select(OBISRawObservation).where(
            OBISRawObservation.source_record_id == "200003"
        )
    )

    assert stored_record is None