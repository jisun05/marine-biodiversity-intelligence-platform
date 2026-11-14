import asyncio
import json

from collections import Counter, defaultdict

from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.models import Observation
from backend.app.services.worms_service import (
    fetch_worms_taxa,
    resolve_worms_taxon,
)


async def main():
    # Step 1: Retrieve unique scientific names and observations.
    with SessionLocal() as db:
        name_statement = (
            select(Observation.scientific_name)
            .distinct()
            .order_by(Observation.scientific_name)
        )

        names = db.execute(name_statement).scalars().all()

        observation_statement = (
            select(
                Observation.id,
                Observation.scientific_name,
                Observation.source,
            )
            .order_by(Observation.id)
        )

        observations = [
            {
                "observation_id": row.id,
                "original_name": row.scientific_name,
                "source": row.source,
            }
            for row in db.execute(observation_statement)
        ]

    print(f"Retrieved {len(names)} unique scientific names.")
    print(f"Retrieved {len(observations)} observations.")

    results = []

    # Step 2: Resolve each unique name using WoRMS.
    for index, name in enumerate(names, start=1):
        print(f"[{index}/{len(names)}] Checking: {name}")

        result = {
            "original_name": name,
            "status": None,
            "resolved_taxon": None,
            "error": None,
        }

        try:
            records = await fetch_worms_taxa(name)

            if not records:
                result["status"] = "unmatched"

            else:
                try:
                    resolved = resolve_worms_taxon(records)

                    if resolved is None:
                        result["status"] = "unmatched"

                    else:
                        result["resolved_taxon"] = resolved

                        original_status = resolved["original_status"]

                        if original_status == "accepted":
                            result["status"] = "accepted"

                        elif original_status == "unaccepted":
                            result["status"] = "unaccepted"

                        elif original_status == "nomen nudum":
                            result["status"] = "nomen_nudum"

                        else:
                            result["status"] = "other_status"

                except ValueError as error:
                    result["status"] = "ambiguous"
                    result["error"] = str(error)

        except Exception as error:
            result["status"] = "api_error"
            result["error"] = (
                f"{type(error).__name__}: {error}"
            )

        results.append(result)

        # Avoid sending requests too quickly.
        await asyncio.sleep(0.2)

    # Step 3: Build a lookup dictionary for resolved taxa.
    taxonomy_lookup = {
        item["original_name"]: item
        for item in results
    }

    # Step 4: Map each observation to its resolved taxonomy.
    observation_mappings = []

    for observation in observations:
        taxonomy_result = taxonomy_lookup[
            observation["original_name"]
        ]

        resolved = taxonomy_result["resolved_taxon"]

        observation_mappings.append({
            **observation,
            "mapping_status": taxonomy_result["status"],
            "aphia_id": (
                resolved["aphia_id"]
                if resolved else None
            ),
            "canonical_name": (
                resolved["canonical_name"]
                if resolved else None
            ),
            "taxonomic_rank": (
                resolved["taxonomic_rank"]
                if resolved else None
            ),
        })

    # Step 5: Calculate name-level status statistics.
    status_categories = [
        "accepted",
        "unaccepted",
        "nomen_nudum",
        "unmatched",
        "ambiguous",
        "api_error",
        "other_status",
    ]

    status_counts = Counter(
        item["status"] for item in results
    )

    matched_count = (
        status_counts["accepted"]
        + status_counts["unaccepted"]
    )

    # Step 6: Collect unique valid taxa using AphiaID.
    unique_taxa = {}

    for item in results:
        resolved = item["resolved_taxon"]

        if not resolved:
            continue

        aphia_id = resolved.get("aphia_id")

        if aphia_id is None:
            continue

        unique_taxa.setdefault(
            aphia_id,
            {
                "aphia_id": aphia_id,
                "canonical_name": resolved["canonical_name"],
                "taxonomic_rank": resolved["taxonomic_rank"],
            },
        )

    rank_counts = Counter(
        taxon["taxonomic_rank"]
        for taxon in unique_taxa.values()
        if taxon["taxonomic_rank"]
    )

    # Step 7: Calculate observation-level statistics.
    observation_status_counts = Counter(
        item["mapping_status"]
        for item in observation_mappings
    )

    total_observations = len(observation_mappings)

    mapped_observations = sum(
        observation_status_counts[status]
        for status in ("accepted", "unaccepted")
    )

    nomen_nudum_observations = (
        observation_status_counts["nomen_nudum"]
    )

    mapping_coverage = (
        mapped_observations / total_observations * 100
        if total_observations > 0
        else 0
    )

    # Step 8: Aggregate observations by AphiaID.
    taxon_observation_counts = {}

    for observation in observation_mappings:
        aphia_id = observation["aphia_id"]

        if aphia_id is None:
            continue

        if aphia_id not in taxon_observation_counts:
            taxon_observation_counts[aphia_id] = {
                "aphia_id": aphia_id,
                "canonical_name": observation["canonical_name"],
                "taxonomic_rank": observation["taxonomic_rank"],
                "total_observations": 0,
                "source_counts": Counter(),
            }

        taxon_observation_counts[aphia_id][
            "total_observations"
        ] += 1

        taxon_observation_counts[aphia_id][
            "source_counts"
        ][observation["source"]] += 1

    taxon_summary = []

    for taxon in taxon_observation_counts.values():
        taxon_summary.append({
            "aphia_id": taxon["aphia_id"],
            "canonical_name": taxon["canonical_name"],
            "taxonomic_rank": taxon["taxonomic_rank"],
            "total_observations": taxon["total_observations"],
            "source_counts": dict(taxon["source_counts"]),
        })

    taxon_summary.sort(
        key=lambda item: item["total_observations"],
        reverse=True,
    )

    # Step 9: Calculate source-level statistics.
    source_status_counts = defaultdict(Counter)

    for observation in observation_mappings:
        source = observation["source"]
        status = observation["mapping_status"]

        source_status_counts[source][status] += 1

    source_summary = {
        source: dict(counts)
        for source, counts in source_status_counts.items()
    }

    # Step 10: Print summary report.
    print("\n" + "=" * 60)
    print("TAXONOMY DRY RUN REPORT")
    print("=" * 60)

    print(f"Total unique names:  {len(names)}")
    print(f"Matched names:       {matched_count}")
    print(f"  Accepted:          {status_counts['accepted']}")
    print(f"  Unaccepted:        {status_counts['unaccepted']}")
    print(f"Nomen nudum:         {status_counts['nomen_nudum']}")
    print(f"Unmatched:           {status_counts['unmatched']}")
    print(f"Ambiguous:           {status_counts['ambiguous']}")
    print(f"API errors:          {status_counts['api_error']}")

    print("\nUnique Taxa:")
    print(f"  Unique AphiaIDs:   {len(unique_taxa)}")

    print("\nTaxonomic ranks:")

    for rank, count in sorted(rank_counts.items()):
        print(f"  {rank}: {count}")

    print("\n" + "=" * 60)
    print("OBSERVATION-LEVEL MAPPING REPORT")
    print("=" * 60)

    print(f"Total observations:       {total_observations}")
    print(f"Mapped observations:      {mapped_observations}")
    print(f"Nomen nudum observations: {nomen_nudum_observations}")
    print(
        f"Unmatched observations:   "
        f"{observation_status_counts['unmatched']}"
    )
    print(
        f"Ambiguous observations:   "
        f"{observation_status_counts['ambiguous']}"
    )
    print(
        f"API error observations:   "
        f"{observation_status_counts['api_error']}"
    )

    print(f"Mapping coverage:         {mapping_coverage:.2f}%")

    print("\nObservations by source:")

    for source, counts in sorted(source_summary.items()):
        print(f"\n  {source}")

        for status, count in sorted(counts.items()):
            print(f"    {status}: {count}")

    print("\nObservations by taxon:")

    for taxon in taxon_summary:
        print(
            f"  {taxon['canonical_name']} "
            f"(AphiaID: {taxon['aphia_id']})"
        )
        print(
            f"    Rank: {taxon['taxonomic_rank']}"
        )
        print(
            f"    Total observations: "
            f"{taxon['total_observations']}"
        )
        print(
            f"    Sources: {taxon['source_counts']}"
        )

    # Step 11: Save the original taxonomy dry run report.
    dry_run_report_path = "taxonomy_dry_run_report.json"

    with open(dry_run_report_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "total_unique_names": len(names),
                "status_counts": {
                    status: status_counts[status]
                    for status in status_categories
                },
                "matched_names": matched_count,
                "unique_taxa_count": len(unique_taxa),
                "unique_taxa": list(unique_taxa.values()),
                "rank_counts": dict(rank_counts),
                "results": results,
                "database_changes": False,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    # Step 12: Save the observation-level mapping plan.
    mapping_plan_path = "taxonomy_observation_mapping_plan.json"

    with open(mapping_plan_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "total_observations": total_observations,
                "mapped_observations": mapped_observations,
                "mapping_coverage_percent": round(
                    mapping_coverage, 2
                ),
                "observation_status_counts": dict(
                    observation_status_counts
                ),
                "source_summary": source_summary,
                "taxon_summary": taxon_summary,
                "observation_mappings": observation_mappings,
                "database_changes": False,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 60)
    print("DATABASE CHANGES: NONE")
    print(f"Dry run report: {dry_run_report_path}")
    print(f"Mapping plan:   {mapping_plan_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())