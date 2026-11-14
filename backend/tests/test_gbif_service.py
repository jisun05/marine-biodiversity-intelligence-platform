import httpx
import pytest

from backend.app.services.gbif_service import (
    fetch_gbif_occurrences,
    GBIF_API_URL,
)


@pytest.mark.anyio
async def test_fetch_gbif_single_page(monkeypatch):
    requested_params = []

    def mock_handler(request):
        params = dict(request.url.params)
        requested_params.append(params)

        return httpx.Response(
            200,
            json={
                "count": 2,
                "offset": 0,
                "limit": 300,
                "results": [
                    {"gbifID": "100001"},
                    {"gbifID": "100002"},
                ],
            },
        )

    transport = httpx.MockTransport(mock_handler)

    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.gbif_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_gbif_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=10,
    )

    assert len(result["results"]) == 2
    assert requested_params[0]["scientificName"] == (
        "Balaenoptera musculus"
    )


@pytest.mark.anyio
async def test_fetch_gbif_rejects_invalid_limit():
    with pytest.raises(ValueError):
        await fetch_gbif_occurrences(
            scientific_name="Balaenoptera musculus",
            limit=0,
        )


@pytest.mark.anyio
async def test_fetch_gbif_api_error(monkeypatch):
    def mock_handler(request):
        return httpx.Response(500)

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.gbif_service.httpx.AsyncClient",
        mock_client,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_gbif_occurrences(
            scientific_name="Balaenoptera musculus",
            limit=10,
        )


@pytest.mark.anyio
async def test_fetch_gbif_multiple_pages(monkeypatch):
    requested_offsets = []
    total_records = 750

    def mock_handler(request):
        params = request.url.params

        offset = int(params["offset"])
        page_limit = int(params["limit"])

        requested_offsets.append(offset)

        remaining = total_records - offset
        result_count = min(page_limit, remaining)

        results = [
            {"gbifID": str(offset + i + 1)}
            for i in range(result_count)
        ]

        return httpx.Response(
            200,
            json={
                "count": total_records,
                "offset": offset,
                "limit": page_limit,
                "results": results,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.gbif_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_gbif_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=750,
    )

    assert len(result["results"]) == 750
    assert requested_offsets == [0, 300, 600]

@pytest.mark.anyio
async def test_fetch_gbif_stops_when_page_is_empty(monkeypatch):
    requested_offsets = []

    def mock_handler(request):
        offset = int(request.url.params["offset"])
        requested_offsets.append(offset)

        if offset == 0:
            results = [
                {"gbifID": str(i)}
                for i in range(300)
            ]
        else:
            results = []

        return httpx.Response(
            200,
            json={
                "count": 750,
                "offset": offset,
                "limit": 300,
                "results": results,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.gbif_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_gbif_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=750,
    )

    assert len(result["results"]) == 300
    assert requested_offsets == [0, 300]
    assert result["count"] == 750