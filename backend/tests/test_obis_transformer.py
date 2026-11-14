from backend.app.models.obis_raw_observation import OBISRawObservation
from backend.app.models.observation import Observation
from datetime import date, datetime
from backend.app.services.obis_transformer import (
    parse_obis_event_date,
    transform_obis_observations,
)


def test_transform_only_matching_species(db_session):
    db_session.add_all([
        OBISRawObservation(
            source_record_id="OBIS_WHALE_001",
            raw_data={
                "id": "OBIS_WHALE_001",
                "scientificName": "Balaenoptera musculus",
                "decimalLatitude": 35.0,
                "decimalLongitude": 129.0,
            },
        ),
        OBISRawObservation(
            source_record_id="OBIS_DOLPHIN_001",
            raw_data={
                "id": "OBIS_DOLPHIN_001",
                "scientificName": "Delphinus delphis",
                "decimalLatitude": 36.0,
                "decimalLongitude": 130.0,
            },
        ),
    ])

    db_session.commit()

    result = transform_obis_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    assert result["fetched"] == 1
    assert result["inserted"] == 1
    assert result["skipped"] == 0

    whale = db_session.query(Observation).filter_by(
        source_record_id="OBIS_WHALE_001"
    ).one()

    assert whale.scientific_name == "Balaenoptera musculus"

    dolphin = db_session.query(Observation).filter_by(
        source_record_id="OBIS_DOLPHIN_001"
    ).first()

    assert dolphin is None


def test_transform_skips_existing_observations(db_session):
    db_session.add(
        OBISRawObservation(
            source_record_id="OBIS_WHALE_002",
            raw_data={
                "id": "OBIS_WHALE_002",
                "scientificName": "Balaenoptera musculus",
                "decimalLatitude": 35.0,
                "decimalLongitude": 129.0,
            },
        )
    )

    db_session.commit()

    first_result = transform_obis_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    second_result = transform_obis_observations(
        db_session,
        scientific_name="Balaenoptera musculus",
    )

    assert first_result["inserted"] == 1
    assert second_result["inserted"] == 0
    assert second_result["skipped"] == 1


def test_parse_obis_iso_date():
    result = parse_obis_event_date("2019-11-11")

    assert result.isoformat() == "2019-11-11"


def test_parse_obis_slash_date():
    result = parse_obis_event_date("13/11/2019")

    assert result.isoformat() == "2019-11-13"


def test_parse_obis_invalid_date():
    result = parse_obis_event_date("invalid")

    assert result is None
def test_parse_obis_date_object():
    result = parse_obis_event_date(date(2019, 11, 11))
    assert result == date(2019, 11, 11)


def test_parse_obis_datetime_object():
    result = parse_obis_event_date(
        datetime(2019, 11, 11, 12, 30)
    )
    assert result == date(2019, 11, 11)


def test_parse_obis_invalid_partial_date():
    assert parse_obis_event_date("2025-05") is None