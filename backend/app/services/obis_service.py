from typing import Any

import httpx


OBIS_API_URL = "https://api.obis.org/v3/occurrence"
OBIS_PAGE_SIZE = 300
MAX_RECORDS = 10_000


async def fetch_obis_occurrences(
    scientific_name: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Fetch occurrence records from the OBIS API using cursor pagination.

    Args:
        scientific_name: Scientific name of the target species.
        limit: Maximum number of records to retrieve.

    Returns:
        OBIS API response as a dictionary.
    """

    if not 1 <= limit <= MAX_RECORDS:
        raise ValueError(
            f"Limit must be between 1 and {MAX_RECORDS}."
        )

    all_results = []
    first_response = None
    after = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(all_results) < limit:
            remaining = limit - len(all_results)
            page_size = min(OBIS_PAGE_SIZE, remaining)

            params = {
                "scientificname": scientific_name,
                "size": page_size,
            }

            if after is not None:
                params["after"] = after

            response = await client.get(
                OBIS_API_URL,
                params=params,
            )

            response.raise_for_status()

            page_data = response.json()

            if first_response is None:
                first_response = page_data

            page_results = page_data["results"]

            if not page_results:
                break

            all_results.extend(page_results)

            if len(all_results) >= limit:
                break

            if len(page_results) < page_size:
                break

            after = page_results[-1].get("id")

            if not after:
                raise ValueError(
                    "OBIS response is missing the last record ID "
                    "required for pagination."
                )

    result = first_response or {"total": 0}
    result["results"] = all_results

    return result