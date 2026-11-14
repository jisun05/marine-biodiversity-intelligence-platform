from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.app.models.obis_raw_observation import OBISRawObservation
from backend.app.models.observation import Observation


def parse_obis_event_date(
    value: str | date | datetime | None,
) -> date | None:
    """
    Parse OBIS event dates into Python date objects.
    Supports ISO 8601 and DD/MM/YYYY formats.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    value = value.strip()

    # ISO 8601 format
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass

    # OBIS format: DD/MM/YYYY
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        pass

    return None

def transform_obis_record(record: dict) -> dict:
    """
    Transform an OBIS raw occurrence record
    into the canonical observation format.
    """

    event_date = parse_obis_event_date(record.get("eventDate"))

    return {
        "source": "OBIS",
        "source_record_id": str(record["id"]),
        "scientific_name": record.get("scientificName"),
        "taxon_id": record.get("scientificNameID"),
        "basis_of_record": record.get("basisOfRecord"),
        "event_date": event_date,
        "latitude": record.get("decimalLatitude"),
        "longitude": record.get("decimalLongitude"),
        "coordinate_uncertainty_m": record.get(
            "coordinateUncertaintyInMeters"
        ),
        "country_code": record.get("countryCode"),
        "dataset_id": record.get("dataset_id"),
    }

def transform_obis_observations(
    db: Session,
    scientific_name: str | None = None,
) -> dict[str, int]:
    """
    Transform stored OBIS raw records into canonical observations.

    If scientific_name is provided, only matching records are transformed.
    """

    query = select(OBISRawObservation)

    if scientific_name:
        query = query.where(
            OBISRawObservation.raw_data["scientificName"]
            .astext.ilike(f"%{scientific_name}%")
        )

    raw_records = db.scalars(query).all()

    try:
        observation_data_list = [
            transform_obis_record(raw_record.raw_data)
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