import re
from typing import Any
from urllib.parse import quote

import httpx

WORMS_API_URL = (
    "https://www.marinespecies.org/rest/"
    "AphiaRecordsByName"
)
def normalize_scientific_name(scientific_name: str) -> str:
    """
    Remove taxonomic authority citations from a scientific name.

    Preserve the original scientific name in the Observation model.
    This function only prepares the name for WoRMS lookup.
    """

    if not scientific_name or not scientific_name.strip():
        raise ValueError("Scientific name must not be empty.")

    name = scientific_name.strip()

    # Remove parenthesized authority citations.
    name = re.sub(
        r"\s*\([^()]*\b(?:17|18|19|20)\d{2}[a-z]?\)\s*$",
        "",
        name,
    )

    # Remove trailing authority citations such as:
    # Ichihara, 1966
    name = re.sub(
        r"\s+[A-Z][A-Za-zÀ-ÿ-]+(?:\s+[A-Z][A-Za-zÀ-ÿ-]+)*,\s*"
        r"(?:17|18|19|20)\d{2}[a-z]?\s*$",
        "",
        name,
    )

    return name.strip()

async def fetch_worms_taxa(
    scientific_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch taxonomic records from WoRMS.

    First search using the original scientific name.
    If no records are found, retry using the normalized name.
    """

    if not scientific_name or not scientific_name.strip():
        raise ValueError("Scientific name must not be empty.")

    params = {
        "like": "false",
        "marine_only": "true",
    }

    timeout = httpx.Timeout(
        60.0,
        connect=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:

        async def search_taxon(
            name: str,
        ) -> list[dict[str, Any]]:
            url = f"{WORMS_API_URL}/{quote(name, safe='')}"

            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

            if response.status_code == 204:
                return []

            data = response.json()

            if not isinstance(data, list):
                raise ValueError(
                    "Unexpected response format from WoRMS API."
                )

            return data

        # First attempt: original scientific name.
        records = await search_taxon(scientific_name.strip())

        if records:
            return records

        # Second attempt: normalized scientific name.
        normalized_name = normalize_scientific_name(
            scientific_name
        )

        if normalized_name == scientific_name.strip():
            return []

        return await search_taxon(normalized_name)


def resolve_worms_taxon(
    records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Resolve WoRMS search results to a single accepted taxon.

    Returns:
        Normalized taxonomy information, or None if no valid
        taxonomic mapping can be established.

    Raises:
        ValueError: If multiple accepted taxa or valid taxa
                    are found.
    """

    if not records:
        return None
        # Case 0: Taxa without valid nomenclatural status.
    nomen_nudum_records = [
        record
        for record in records
        if record.get("status") == "nomen nudum"
    ]

    if nomen_nudum_records:
        if len(nomen_nudum_records) > 1:
            raise ValueError(
                "Multiple nomen nudum records found. "
                "Manual review is required."
            )

        record = nomen_nudum_records[0]

        return {
            "aphia_id": None,
            "canonical_name": None,
            "authority": record.get("authority"),
            "taxonomic_rank": record.get("rank"),
            "parent_aphia_id": record.get("parentNameUsageID"),
            "original_aphia_id": record.get("AphiaID"),
            "original_name": record.get("scientificname"),
            "original_status": "nomen nudum",
            "unaccept_reason": record.get("unacceptreason"),
            "match_type": record.get("match_type"),
        }
    accepted_records = [
        record
        for record in records
        if record.get("status") == "accepted"
        and record.get("AphiaID") is not None
    ]

    # Case 1: Exactly one accepted taxon.
    if len(accepted_records) == 1:
        record = accepted_records[0]

        return {
            "aphia_id": record["AphiaID"],
            "canonical_name": record["scientificname"],
            "authority": record.get("authority"),
            "taxonomic_rank": record.get("rank"),
            "parent_aphia_id": record.get("parentNameUsageID"),
            "original_aphia_id": record["AphiaID"],
            "original_name": record["scientificname"],
            "original_status": "accepted",
            "match_type": record.get("match_type"),
        }

    # Case 2: Multiple accepted taxa are ambiguous.
    if len(accepted_records) > 1:
        raise ValueError(
            "Multiple accepted taxa found. "
            "Manual review is required."
        )

    # Case 3: No accepted record.
    valid_taxa = {}

    for record in records:
        valid_aphia_id = record.get("valid_AphiaID")
        valid_name = record.get("valid_name")

        if (
            record.get("status") == "unaccepted"
            and valid_aphia_id is not None
            and valid_name
        ):
            valid_taxa[valid_aphia_id] = record

    if not valid_taxa:
        return None

    # Multiple valid taxa are ambiguous.
    if len(valid_taxa) > 1:
        raise ValueError(
            "Multiple valid taxa found. "
            "Manual review is required."
        )

    # Exactly one valid taxon.
    original_record = next(iter(valid_taxa.values()))

    return {
        "aphia_id": original_record["valid_AphiaID"],
        "canonical_name": original_record["valid_name"],
        "authority": original_record.get("valid_authority"),
        "taxonomic_rank": original_record.get("rank"),
        "parent_aphia_id": original_record.get("parentNameUsageID"),
        "original_aphia_id": original_record.get("AphiaID"),
        "original_name": original_record.get("scientificname"),
        "original_status": "unaccepted",
        "match_type": original_record.get("match_type"),
    }