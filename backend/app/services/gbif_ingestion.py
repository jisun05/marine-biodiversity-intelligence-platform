from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from backend.app.models.gbif_raw_observation import GBIFRawObservation
from backend.app.services.gbif_service import fetch_gbif_occurrences


async def ingest_gbif_occurrences(
    db: Session,
    scientific_name: str,
    limit: int = 10,
) -> dict[str, int]:
    """
    Fetch GBIF occurrence records and store the original JSON responses.

    Existing records are skipped using their GBIF occurrence IDs.
    """

    # Fetch records from GBIF API
    data = await fetch_gbif_occurrences(
        scientific_name=scientific_name,
        limit=limit,
    )

    records = data["results"]

    try:
        inserted = 0
        batch_size = 500

        for start in range(0, len(records), batch_size):
            batch_records = records[start:start + batch_size]

            raw_observations = [
                {
                    "source_record_id": str(record["gbifID"]),
                    "raw_data": record,
                }
                for record in batch_records
            ]

            if not raw_observations:
                continue

            statement = (
                pg_insert(GBIFRawObservation)
                .values(raw_observations)
                .on_conflict_do_nothing(
                    index_elements=[
                        GBIFRawObservation.source_record_id
                    ]
                )
                .returning(GBIFRawObservation.id)
            )

            result = db.execute(statement)
            inserted += len(result.scalars().all())

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "fetched": len(records),
        "inserted": inserted,
        "skipped": len(records) - inserted,
    }