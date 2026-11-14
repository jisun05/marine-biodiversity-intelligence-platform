from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from datetime import date, datetime
from backend.app.models.gbif_raw_observation import GBIFRawObservation
from backend.app.models.observation import Observation


def parse_gbif_event_date(value: str | date | None) -> date | None:
    """
    Parse GBIF event dates into Python date objects.
    Incomplete or invalid dates return None.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None

def transform_gbif_record(record: dict) -> dict:
    """
    Transform a GBIF raw occurrence record
    into the canonical observation format.
    """

    event_date = parse_gbif_event_date(record.get("eventDate"))

    return {
        "source": "GBIF",
        "source_record_id": str(record["gbifID"]),
        "scientific_name": record.get("scientificName"),
        "taxon_id": (
            str(record["taxonKey"])
            if record.get("taxonKey") is not None
            else None
        ),
        "basis_of_record": record.get("basisOfRecord"),
        "event_date": event_date,
        "latitude": record.get("decimalLatitude"),
        "longitude": record.get("decimalLongitude"),
        "coordinate_uncertainty_m": record.get(
            "coordinateUncertaintyInMeters"
        ),
        "country_code": record.get("countryCode"),
        "dataset_id": record.get("datasetKey"),
    }


def transform_gbif_observations(
    db: Session,
    scientific_name: str | None = None,
) -> dict[str, int]:
    """
    Transform stored GBIF raw records into canonical observations.

    If scientific_name is provided, only matching records are transformed.
    Partial matching supports GBIF scientific names containing authorship
    information or subspecies names.
    """

    query = select(GBIFRawObservation)

    if scientific_name:
        query = query.where(
            GBIFRawObservation.raw_data["scientificName"]
            .astext.ilike(f"%{scientific_name}%")
        )

    raw_records = db.scalars(query).all()

    try:
        observation_data_list = [
            transform_gbif_record(raw_record.raw_data)
            for raw_record in raw_records
        ]

        inserted = 0
        batch_size = 500

        for start in range(0, len(observation_data_list), batch_size):
            batch = observation_data_list[
                start:start + batch_size
            ]

            if not batch:
                continue

            statement = (
                pg_insert(Observation)
                .values(batch)
                .on_conflict_do_nothing(
                    index_elements=[
                        Observation.source,
                        Observation.source_record_id,
                    ]
                )
                .returning(Observation.id)
            )

            result = db.execute(statement)
            inserted += len(result.scalars().all())

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "fetched": len(raw_records),
        "inserted": inserted,
        "skipped": len(raw_records) - inserted,
    }