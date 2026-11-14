from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.data_collection import DataCollection
from backend.app.services.data_collection_service import collect_species_data


async def process_batch(
    db: Session,
    scientific_names: list[str],
    sources: list[str],
    limit: int = 10,
) -> list[DataCollection]:

    collections = []

    for scientific_name in scientific_names:
        collection = DataCollection(
            scientific_name=scientific_name,
            sources=sources,
            trigger_type="manual",
            status="pending",
        )

        db.add(collection)
        db.commit()
        db.refresh(collection)

        try:
            collection.status = "running"
            db.commit()

            result = await collect_species_data(
                db=db,
                scientific_name=scientific_name,
                sources=sources,
                limit=limit,
            )

            collection.status = result["status"]
            collection.total_fetched = result["total_fetched"]
            collection.total_inserted = result["total_inserted"]
            collection.total_transformed = result["total_transformed"]

            if result["failed_sources"]:
                collection.error_message = "; ".join(
                    f'{item["source"]}: {item["error"]}'
                    for item in result["failed_sources"]
                )

        except Exception as error:
            db.rollback()

            collection.status = "failed"
            collection.error_message = str(error)

        finally:
            collection.completed_at = datetime.now(timezone.utc)
            db.add(collection)
            db.commit()
            db.refresh(collection)

        collections.append(collection)

    return collections