from backend.app.models.gbif_raw_observation import GBIFRawObservation
from backend.app.services.gbif_transformer import (
    transform_gbif_observations,   parse_gbif_event_date,
)
from backend.app.models.observation import Observation


def test_transform_only_matching_species(db_session):
    db_session.add_all([
        GBIFRawObservation(
            source_record_id="GBIF_WHALE_001",
            raw_data={
                "gbifID": "GBIF_WHALE_001",
                "scientificName": (
                    "Balaenoptera musculus "
                    "intermedia Burmeister, 1871"
                ),
                "decimalLatitude": 35.0,
                "decimalLongitude": 129.0,
            },
        ),
        GBIFRawObservation(
            source_record_id="GBIF_DOLPHIN_001",
            raw_data={
                "gbifID": "GBIF_DOLPHIN_001",
                "scientificName": "Delphinus delphis",
                "decimalLatitude": 36.0,
                "decimalLongitude": 130.0,
            },
        ),
    ])

    db_session.commit()

    result = transform_gbif_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    assert result["fetched"] == 1
    assert result["inserted"] == 1
    assert result["skipped"] == 0

    whale = db_session.query(Observation).filter_by(
        source_record_id="GBIF_WHALE_001"
    ).one()

    assert "Balaenoptera musculus" in whale.scientific_name

    dolphin = db_session.query(Observation).filter_by(
        source_record_id="GBIF_DOLPHIN_001"
    ).first()

    assert dolphin is None


def test_transform_skips_existing_observations(db_session):
    db_session.add(
        GBIFRawObservation(
            source_record_id="GBIF_WHALE_002",
            raw_data={
                "gbifID": "GBIF_WHALE_002",
                "scientificName": "Balaenoptera musculus",
                "decimalLatitude": 35.0,
                "decimalLongitude": 129.0,
            },
        )
    )

    db_session.commit()

    first_result = transform_gbif_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    second_result = transform_gbif_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    assert first_result["inserted"] == 1
    assert second_result["inserted"] == 0
    assert second_result["skipped"] == 1



def test_parse_gbif_incomplete_year():
    assert parse_gbif_event_date("2024") is None


def test_parse_gbif_incomplete_month():
    assert parse_gbif_event_date("2025-05") is None


def test_parse_gbif_invalid_date():
    assert parse_gbif_event_date("invalid") is None


def test_parse_gbif_iso_datetime():
    result = parse_gbif_event_date("2025-07-14T12:30:00")
    assert result.isoformat() == "2025-07-14"

def test_parse_gbif_incomplete_year():
    assert parse_gbif_event_date("2024") is None


def test_parse_gbif_incomplete_month():
    assert parse_gbif_event_date("2025-05") is None


def test_parse_gbif_invalid_date():
    assert parse_gbif_event_date("invalid") is None


def test_parse_gbif_iso_datetime():
    result = parse_gbif_event_date("2025-07-14T12:30:00")
    assert result.isoformat() == "2025-07-14"