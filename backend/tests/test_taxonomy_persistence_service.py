import pytest

from backend.app.models import Observation, ObservationTaxonomy, Taxon
from backend.app.services.taxonomy_persistence_service import (
    persist_taxonomy_mapping,
)


def get_test_observation(db, source_record_id="GBIF_TEST_1"):
    return db.query(Observation).filter_by(
        source_record_id=source_record_id
    ).one()


def test_persist_new_taxon_and_mapping(db_session):
    observation = get_test_observation(db_session)

    resolved_taxon = {
        "aphia_id": 9000001,
        "canonical_name": "Thunnus albacares",
        "authority": "Bonnaterre, 1788",
        "taxonomic_rank": "Species",
        "parent_aphia_id": 127027,
        "match_type": "exact",
        "original_status": "accepted",
    }

    mapping = persist_taxonomy_mapping(
        db_session,
        observation.id,
        resolved_taxon,
    )

    taxon = db_session.get(Taxon, 9000001)

    assert taxon is not None
    assert taxon.canonical_name == "Thunnus albacares"
    assert taxon.taxonomic_rank == "Species"

    assert mapping.observation_id == observation.id
    assert mapping.aphia_id == 9000001
    assert mapping.taxonomy_source == "WORMS"


def test_reuse_existing_taxon_for_multiple_observations(db_session):
    first_observation = get_test_observation(
        db_session, "GBIF_TEST_1"
    )
    second_observation = get_test_observation(
        db_session, "GBIF_TEST_2"
    )

    resolved_taxon = {
        "aphia_id": 9000002,
        "canonical_name": "Thunnus albacares",
        "authority": "Bonnaterre, 1788",
        "taxonomic_rank": "Species",
    }

    persist_taxonomy_mapping(
        db_session,
        first_observation.id,
        resolved_taxon,
    )

    persist_taxonomy_mapping(
        db_session,
        second_observation.id,
        resolved_taxon,
    )

    taxon_count = (
        db_session.query(Taxon)
        .filter_by(aphia_id=9000002)
        .count()
    )

    mapping_count = (
        db_session.query(ObservationTaxonomy)
        .filter_by(aphia_id=9000002)
        .count()
    )

    assert taxon_count == 1
    assert mapping_count == 2


def test_update_existing_observation_mapping(db_session):
    observation = get_test_observation(db_session)

    first_taxon = {
        "aphia_id": 9000003,
        "canonical_name": "Thunnus albacares",
        "taxonomic_rank": "Species",
        "match_type": "exact",
        "original_status": "accepted",
    }

    updated_taxon = {
        "aphia_id": 9000004,
        "canonical_name": "Thunnus obesus",
        "taxonomic_rank": "Species",
        "match_type": "exact",
        "original_status": "unaccepted",
    }

    persist_taxonomy_mapping(
        db_session,
        observation.id,
        first_taxon,
    )

    persist_taxonomy_mapping(
        db_session,
        observation.id,
        updated_taxon,
    )

    mapping = db_session.get(
        ObservationTaxonomy,
        observation.id,
    )

    assert mapping.aphia_id == 9000004
    assert mapping.match_type == "exact"
    assert mapping.original_status == "unaccepted"


def test_reject_missing_required_fields(db_session):
    observation = get_test_observation(db_session)

    incomplete_taxon = {
        "aphia_id": 9000005,
        "canonical_name": "Thunnus albacares",
    }

    with pytest.raises(
        ValueError,
        match="Missing required taxonomy fields",
    ):
        persist_taxonomy_mapping(
            db_session,
            observation.id,
            incomplete_taxon,
        )

    assert db_session.get(Taxon, 9000005) is None


def test_persist_same_mapping_twice_without_duplicates(db_session):
    observation = get_test_observation(db_session)

    resolved_taxon = {
        "aphia_id": 9000006,
        "canonical_name": "Thunnus albacares",
        "taxonomic_rank": "Species",
        "match_type": "exact",
        "original_status": "accepted",
    }

    persist_taxonomy_mapping(
        db_session,
        observation.id,
        resolved_taxon,
    )

    persist_taxonomy_mapping(
        db_session,
        observation.id,
        resolved_taxon,
    )

    taxon_count = (
        db_session.query(Taxon)
        .filter_by(aphia_id=9000006)
        .count()
    )

    mapping_count = (
        db_session.query(ObservationTaxonomy)
        .filter_by(observation_id=observation.id)
        .count()
    )

    assert taxon_count == 1
    assert mapping_count == 1
