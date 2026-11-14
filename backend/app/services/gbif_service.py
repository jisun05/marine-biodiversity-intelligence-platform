from typing import Any

import httpx


GBIF_API_URL = "https://api.gbif.org/v1/occurrence/search"

GBIF_PAGE_SIZE = 300
MAX_RECORDS = 10_000


async def fetch_gbif_occurrences(
    scientific_name: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Fetch occurrence records from the GBIF API using pagination.

    Args:
        scientific_name: Scientific name of the target species.
        limit: Maximum total number of records to retrieve.

    Returns:
        GBIF API response with combined occurrence records.
    """

    if not 1 <= limit <= MAX_RECORDS:
        raise ValueError(
            f"Limit must be between 1 and {MAX_RECORDS}."
        )

    all_results = []
    total_count = 0
    first_response = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(all_results) < limit:
            remaining = limit - len(all_results)
            page_limit = min(GBIF_PAGE_SIZE, remaining)

            params = {
                "scientificName": scientific_name,
                "hasCoordinate": "true",
                "limit": page_limit,
                "offset": len(all_results),
            }

            response = await client.get(
                GBIF_API_URL,
                params=params,
            )

            response.raise_for_status()

            page_data = response.json()

            if first_response is None:
                first_response = page_data
                total_count = page_data["count"]

            page_results = page_data["results"]

            if not page_results:
                break

            all_results.extend(page_results)

            if len(all_results) >= total_count:
                break

    result = first_response or {
        "count": 0,
        "offset": 0,
        "limit": limit,
    }

    result["results"] = all_results
    result["offset"] = 0
    result["limit"] = limit

    return result