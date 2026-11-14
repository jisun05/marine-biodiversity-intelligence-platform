import httpx
import pytest

from backend.app.services.obis_service import (
    fetch_obis_occurrences,
)


@pytest.mark.anyio
async def test_fetch_obis_single_page(monkeypatch):
    requested_params = []

    def mock_handler(request):
        params = dict(request.url.params)
        requested_params.append(params)

        return httpx.Response(
            200,
            json={
                "total": 2,
                "results": [
                    {"id": "obis-100001"},
                    {"id": "obis-100002"},
                ],
            },
        )

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.obis_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_obis_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=10,
    )

    assert len(result["results"]) == 2
    assert requested_params[0]["scientificname"] == (
        "Balaenoptera musculus"
    )
    assert "after" not in requested_params[0]


@pytest.mark.anyio
async def test_fetch_obis_multiple_pages(monkeypatch):
    requested_params = []
    total_records = 750

    def mock_handler(request):
        params = request.url.params
        requested_params.append(dict(params))

        after = params.get("after")

        if after is None:
            start = 0
        else:

            cursor_starts = {
                None: 0,
                "obis-300": 300,
                "obis-600": 600,
            }

            start = cursor_starts[after]

        remaining = total_records - start
        result_count = min(300, remaining)

        results = [
            {"id": f"obis-{i + 1}"}
            for i in range(start, start + result_count)
        ]

        return httpx.Response(
            200,
            json={
                "total": total_records,
                "results": results,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.obis_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_obis_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=750,
    )

    assert len(result["results"]) == 750
    assert len(requested_params) == 3
    assert "after" not in requested_params[0]
    assert requested_params[1]["after"] == "obis-300"
    assert requested_params[2]["after"] == "obis-600"
    assert requested_params[0]["size"] == "300"
    assert requested_params[1]["size"] == "300"
    assert requested_params[2]["size"] == "150"



@pytest.mark.anyio
async def test_fetch_obis_rejects_invalid_limit():
    with pytest.raises(ValueError):
        await fetch_obis_occurrences(
            scientific_name="Balaenoptera musculus",
            limit=0,
        )


@pytest.mark.anyio
async def test_fetch_obis_api_error(monkeypatch):
    def mock_handler(request):
        return httpx.Response(500)

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.obis_service.httpx.AsyncClient",
        mock_client,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_obis_occurrences(
            scientific_name="Balaenoptera musculus",
            limit=10,
        )

@pytest.mark.anyio
async def test_fetch_obis_stops_when_page_is_empty(monkeypatch):
    requested_params = []

    def mock_handler(request):
        params = request.url.params
        requested_params.append(dict(params))

        if params.get("after") is None:
            results = [
                {"id": f"obis-{i}"}
                for i in range(300)
            ]
        else:
            results = []

        return httpx.Response(
            200,
            json={
                "total": 750,
                "results": results,
            },
        )

    transport = httpx.MockTransport(mock_handler)
    original_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        "backend.app.services.obis_service.httpx.AsyncClient",
        mock_client,
    )

    result = await fetch_obis_occurrences(
        scientific_name="Balaenoptera musculus",
        limit=750,
    )

    assert len(result["results"]) == 300
    assert len(requested_params) == 2
    assert requested_params[1]["after"] == "obis-299"
