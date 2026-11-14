import pytest

from fastapi.testclient import TestClient
from backend.app.models.observation import Observation

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.db.session import (
    test_engine,
    TestSessionLocal,
    get_db,
)


# Import models so SQLAlchemy can register all tables
from backend.app import models


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create database tables before running tests.
    """

    if test_engine is None:
        raise RuntimeError("Test database is not configured.")

    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """
    Provide an isolated database session for each test.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        test_observations = []

        for source in ["GBIF", "OBIS"]:
            for i in range(5):
                observation = Observation(
                    source=source,
                    source_record_id=f"{source}_TEST_{i + 1}",
                    scientific_name="Thunnus albacares",
                    taxon_id="12345",
                    latitude=35.0 + i,
                    longitude=129.0 + i,
                    country_code="KR",
                )

                test_observations.append(observation)

        db.add_all(test_observations)
        db.commit()

        yield db

    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """
    Override FastAPI database dependency.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()