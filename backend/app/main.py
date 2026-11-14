from fastapi import FastAPI

from backend.app.api import (
    health,
    observation_routes,
    data_collection_routes,
    taxonomy_routes,
)

app = FastAPI(
    title="Marine Biodiversity Intelligence Platform",
    description="An API for marine biodiversity observation data.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(observation_routes.router)
app.include_router(data_collection_routes.router)
app.include_router(taxonomy_routes.router)
