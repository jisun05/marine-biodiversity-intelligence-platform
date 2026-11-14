import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal
from backend.app.models import (
    Observation,
    ObservationTaxonomy,
    Taxon,
)
from backend.app.services.taxonomy_persistence_service import (
    persist_taxonomy_mapping,
)


REPORT_PATH = PROJECT_ROOT / "taxonomy_dry_run_report.json"
PLAN_PATH = PROJECT_ROOT / "taxonomy_observation_mapping_plan.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def prepare_mappings():
    report = load_json(REPORT_PATH)
    plan = load_json(PLAN_PATH)

    taxonomy_lookup = {
        item["original_name"]: item
        for item in report["results"]
    }

    observations = plan["observation_mappings"]

    observation_ids = [
        item["observation_id"]
        for item in observations
    ]

    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError("Duplicate observation IDs found.")

    status_counts = Counter(
        item["mapping_status"] for item in observations
    )

    if status_counts != Counter({
        "accepted": 208,
        "nomen_nudum": 2,
    }):
        raise ValueError(
            f"Unexpected mapping status distribution: {status_counts}"
        )

    prepared = []
    skipped = []

    for observation in observations:
        status = observation["mapping_status"]

        if status == "nomen_nudum":
            skipped.append(observation)
            continue

        if status != "accepted":
            raise ValueError(
                f"Unsupported mapping status: {status}"
            )

        result = taxonomy_lookup.get(observation["original_name"])

        if result is None:
            raise ValueError(
                f"Missing WoRMS result: {observation['original_name']}"
            )

        resolved = result.get("resolved_taxon")

        if not resolved:
            raise ValueError(
                f"Missing resolved taxonomy: {observation['original_name']}"
            )

        required_fields = (
            "aphia_id",
            "canonical_name",
            "taxonomic_rank",
            "match_type",
            "original_status",
        )

        missing = [
            field for field in required_fields
            if resolved.get(field) is None
        ]

        if missing:
            raise ValueError(
                f"Missing fields for {observation['original_name']}: {missing}"
            )

        if resolved["original_status"] != "accepted":
            raise ValueError(
                f"Unexpected WoRMS status: {observation['original_name']}"
            )

        if (
            int(resolved["aphia_id"]) != observation["aphia_id"]
            or resolved["canonical_name"] != observation["canonical_name"]
            or resolved["taxonomic_rank"] != observation["taxonomic_rank"]
        ):
            raise ValueError(
                f"Taxonomy mismatch: {observation['original_name']}"
            )

        prepared.append({
            "observation_id": observation["observation_id"],
            "resolved_taxon": resolved,
        })

    unique_aphia_ids = {
        item["resolved_taxon"]["aphia_id"]
        for item in prepared
    }

    if len(prepared) != 208:
        raise ValueError(f"Expected 208 mappings, got {len(prepared)}")

    if len(skipped) != 2:
        raise ValueError(f"Expected 2 skipped records, got {len(skipped)}")

    if len(unique_aphia_ids) != 15:
        raise ValueError(
            f"Expected 15 unique taxa, got {len(unique_aphia_ids)}"
        )

    return prepared, skipped, unique_aphia_ids


def show_preview(prepared, skipped, unique_aphia_ids):
    print("\nTaxonomy persistence preview")
    print("=" * 45)
    print(f"Taxa to persist: {len(unique_aphia_ids)}")
    print(f"Observation mappings: {len(prepared)}")
    print(f"Skipped nomen nudum: {len(skipped)}")
    print("Existing observations to modify: 0")
    print("\nSkipped records:")

    for item in skipped:
        print(
            f"  Observation {item['observation_id']}: "
            f"{item['original_name']}"
        )

    print("\nValidation: PASSED")
    print("Database changes: NONE")


def apply_persistence(prepared):
    db = SessionLocal()

    try:
        observation_ids = [
            item["observation_id"]
            for item in prepared
        ]

        existing_ids = set(
            db.scalars(
                select(Observation.id).where(
                    Observation.id.in_(observation_ids)
                )
            ).all()
        )

        missing_ids = set(observation_ids) - existing_ids

        if missing_ids:
            raise ValueError(
                f"Observations not found in database: {sorted(missing_ids)}"
            )

        before_taxa = db.query(Taxon).count()
        before_mappings = db.query(ObservationTaxonomy).count()
        before_observations = db.query(Observation).count()

        for item in prepared:
            persist_taxonomy_mapping(
                db=db,
                observation_id=item["observation_id"],
                resolved_taxon=item["resolved_taxon"],
            )

        db.flush()

        after_taxa = db.query(Taxon).count()
        after_mappings = db.query(ObservationTaxonomy).count()
        after_observations = db.query(Observation).count()

        if after_observations != before_observations:
            raise RuntimeError(
                "Observation count changed unexpectedly."
            )

        db.commit()

        print("\nDatabase persistence completed.")
        print("=" * 45)
        print(f"Taxa: {before_taxa} -> {after_taxa}")
        print(f"Mappings: {before_mappings} -> {after_mappings}")
        print(
            f"Observations: {before_observations} -> {after_observations}"
        )

    except Exception:
        db.rollback()
        print("\nPersistence failed. Transaction rolled back.")
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Persist WoRMS taxonomy mappings."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to the database. Default is preview only.",
    )
    args = parser.parse_args()

    prepared, skipped, unique_aphia_ids = prepare_mappings()

    show_preview(prepared, skipped, unique_aphia_ids)

    if args.apply:
        print("\nApplying changes to the database...")
        apply_persistence(prepared)
    else:
        print(
            "\nPreview only. Use --apply to persist the mappings."
        )


if __name__ == "__main__":
    main()
