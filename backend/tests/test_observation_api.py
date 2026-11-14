def test_get_all_observations(client):
    response = client.get("/observations")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 10
    assert len(data["items"]) == 10


def test_filter_observations_by_gbif(client):
    response = client.get(
        "/observations",
        params={"source": "GBIF"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert all(
        item["source"] == "GBIF"
        for item in data["items"]
    )


def test_filter_observations_by_obis(client):
    response = client.get(
        "/observations",
        params={"source": "OBIS"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert all(
        item["source"] == "OBIS"
        for item in data["items"]
    )


def test_search_observations_by_scientific_name(client):
    response = client.get(
        "/observations",
        params={"scientific_name": "Thunnus"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 10
    assert all(
        "Thunnus" in item["scientific_name"]
        for item in data["items"]
    )


def test_observation_pagination(client):
    response = client.get(
        "/observations",
        params={"skip": 0, "limit": 3},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 10
    assert len(data["items"]) == 3


def test_invalid_pagination_parameters(client):
    response = client.get(
        "/observations",
        params={"skip": -1, "limit": 200},
    )

    assert response.status_code == 422


def test_invalid_observation_source(client):
    response = client.get(
        "/observations",
        params={"source": "UNKNOWN"},
    )

    assert response.status_code == 422


def test_empty_scientific_name(client):
    response = client.get(
        "/observations",
        params={"scientific_name": ""},
    )

    assert response.status_code == 422