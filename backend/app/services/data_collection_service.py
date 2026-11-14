from sqlalchemy.orm import Session

from backend.app.services.gbif_ingestion import (
    ingest_gbif_occurrences,
)
from backend.app.services.obis_ingestion import (
    ingest_obis_occurrences,
)
from backend.app.services.gbif_transformer import (
    transform_gbif_observations,
)
from backend.app.services.obis_transformer import (
    transform_obis_observations,
)


async def collect_species_data(
    db: Session,
    scientific_name: str,
    sources: list[str],
    limit: int = 10,
) -> dict:
    """
    Collect and transform biodiversity observations
    for a single species from selected data sources.

    Each source is processed independently so that
    a failure in one source does not stop the others.
    """

    total_fetched = 0
    total_inserted = 0
    total_transformed = 0

    successful_sources = []
    failed_sources = []

    source_handlers = {
        "GBIF": (
            ingest_gbif_occurrences,
            transform_gbif_observations,
        ),
        "OBIS": (
            ingest_obis_occurrences,
            transform_obis_observations,
        ),
    }

    for source in sources:
        try:
            ingestion_function, transformer_function = (
                source_handlers[source]
            )

            # Fetch and store raw observations
            ingestion_result = await ingestion_function(
                db=db,
                scientific_name=scientific_name,
                limit=limit,
            )

            total_fetched += ingestion_result["fetched"]
            total_inserted += ingestion_result["inserted"]

            # Transform only the requested species
            transformation_result = transformer_function(
                db=db,
                scientific_name=scientific_name,
            )

            total_transformed += transformation_result["inserted"]

            successful_sources.append(source)

        except Exception as error:
            db.rollback()

            failed_sources.append({
                "source": source,
                "error": str(error),
            })

    if not failed_sources:
        status = "completed"
    elif successful_sources:
        status = "partial"
    else:
        status = "failed"

    return {
        "scientific_name": scientific_name,
        "status": status,
        "total_fetched": total_fetched,
        "total_inserted": total_inserted,
        "total_transformed": total_transformed,
        "successful_sources": successful_sources,
        "failed_sources": failed_sources,
    }