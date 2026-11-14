import asyncio

import pytest

from backend.app.services.worms_service import (
    fetch_worms_taxa,
    resolve_worms_taxon,
    normalize_scientific_name,
)

def test_resolve_accepted_taxon():
    records = [
        {
            "AphiaID": 137090,
            "scientificname": "Balaenoptera musculus",
            "authority": "(Linnaeus, 1758)",
            "status": "accepted",
            "rank": "Species",
            "valid_AphiaID": 137090,
            "valid_name": "Balaenoptera musculus",
            "parentNameUsageID": 137013,
            "match_type": "exact",
        }
    ]

    result = resolve_worms_taxon(records)

    assert result["aphia_id"] == 137090
    assert result["canonical_name"] == "Balaenoptera musculus"
    assert result["original_status"] == "accepted"


def test_resolve_unaccepted_taxon():
    records = [
        {
            "AphiaID": 105857,
            "scientificname": "Manta birostris",
            "authority": "(Walbaum, 1792)",
            "status": "unaccepted",
            "rank": "Species",
            "valid_AphiaID": 1026118,
            "valid_name": "Mobula birostris",
            "valid_authority": "(Walbaum, 1792)",
            "parentNameUsageID": 105755,
            "match_type": "exact",
        }
    ]

    result = resolve_worms_taxon(records)

    assert result["aphia_id"] == 1026118
    assert result["canonical_name"] == "Mobula birostris"
    assert result["original_aphia_id"] == 105857
    assert result["original_name"] == "Manta birostris"
    assert result["original_status"] == "unaccepted"


def test_resolve_empty_records():
    result = resolve_worms_taxon([])

    assert result is None


def test_resolve_multiple_accepted_taxa():
    records = [
        {
            "AphiaID": 137090,
            "scientificname": "Balaenoptera musculus",
            "status": "accepted",
        },
        {
            "AphiaID": 137091,
            "scientificname": "Balaenoptera physalus",
            "status": "accepted",
        },
    ]

    with pytest.raises(ValueError):
        resolve_worms_taxon(records)


def test_fetch_worms_taxa_returns_empty_list_on_204(monkeypatch):
    class MockResponse:
        status_code = 204

        def raise_for_status(self):
            pass

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.services.worms_service.httpx.AsyncClient",
        MockAsyncClient,
    )



    result = asyncio.run(
        fetch_worms_taxa("Unknown marine species")
    )

    assert result == []



@pytest.mark.parametrize(
    ("original", "expected"),
    [
        (
            "Thunnus thynnus (Linnaeus, 1758)",
            "Thunnus thynnus",
        ),
        (
            "Enhydra lutris nereis (Merriam, 1904)",
            "Enhydra lutris nereis",
        ),
        (
            "Balaenoptera musculus brevicauda Ichihara, 1966",
            "Balaenoptera musculus brevicauda",
        ),
        (
            "Thunnus thynnus",
            "Thunnus thynnus",
        ),
    ],
)
def test_normalize_scientific_name(original, expected):
    assert normalize_scientific_name(original) == expected


def test_normalize_empty_scientific_name():
    with pytest.raises(ValueError):
        normalize_scientific_name("")



def test_fetch_worms_taxa_does_not_retry_when_original_name_succeeds(
    monkeypatch,
):
    expected_records = [
        {
            "AphiaID": 127029,
            "scientificname": "Thunnus thynnus",
            "status": "accepted",
        }
    ]

    calls = []

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return expected_records

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, **kwargs):
            calls.append(url)
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.services.worms_service.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = asyncio.run(
        fetch_worms_taxa("Thunnus thynnus")
    )

    assert result == expected_records
    assert len(calls) == 1


def test_fetch_worms_taxa_retries_with_normalized_name(
    monkeypatch,
):
    expected_records = [
        {
            "AphiaID": 127029,
            "scientificname": "Thunnus thynnus",
            "status": "accepted",
        }
    ]

    calls = []

    class MockResponse:
        def __init__(self, status_code, records=None):
            self.status_code = status_code
            self.records = records or []

        def raise_for_status(self):
            pass

        def json(self):
            return self.records

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, **kwargs):
            calls.append(url)

            if len(calls) == 1:
                return MockResponse(204)

            return MockResponse(200, expected_records)

    monkeypatch.setattr(
        "backend.app.services.worms_service.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = asyncio.run(
        fetch_worms_taxa(
            "Thunnus thynnus (Linnaeus, 1758)"
        )
    )

    assert result == expected_records
    assert len(calls) == 2
    assert "Thunnus%20thynnus" in calls[1]


def test_fetch_worms_taxa_does_not_retry_unchanged_name(
    monkeypatch,
):
    calls = []

    class MockResponse:
        status_code = 204

        def raise_for_status(self):
            pass

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, **kwargs):
            calls.append(url)
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.services.worms_service.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = asyncio.run(
        fetch_worms_taxa("Thunnus thynnus")
    )

    assert result == []
    assert len(calls) == 1






def test_resolve_nomen_nudum_taxon():
    records = [
        {
            "AphiaID": 853378,
            "scientificname": "Megaptera novaeangliae australis",
            "status": "nomen nudum",
            "unacceptreason": "No holotype fixed",
            "rank": "Subspecies",
            "valid_AphiaID": None,
            "valid_name": None,
            "parentNameUsageID": 137092,
        }
    ]

    result = resolve_worms_taxon(records)

    assert result["original_status"] == "nomen nudum"
    assert result["original_aphia_id"] == 853378
    assert result["parent_aphia_id"] == 137092
    assert result["canonical_name"] is None
    assert result["aphia_id"] is None


def test_resolve_nomen_nudum_without_parent():
    records = [
        {
            "AphiaID": 853378,
            "scientificname": "Example species",
            "status": "nomen nudum",
            "unacceptreason": "No holotype fixed",
            "rank": "Species",
            "valid_AphiaID": None,
            "valid_name": None,
            "parentNameUsageID": None,
        }
    ]

    result = resolve_worms_taxon(records)

    assert result["original_status"] == "nomen nudum"
    assert result["parent_aphia_id"] is None
    assert result["aphia_id"] is None
