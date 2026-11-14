# Marine Biodiversity Intelligence Platform

An open-source data integration and visualization platform for marine biodiversity observations.

The platform integrates marine biodiversity data from public biodiversity databases, processes and standardizes observation records, stores geospatial information, and provides REST APIs and interactive map-based visualization.

## 1. Project Overview

Marine biodiversity data is distributed across multiple public databases and data providers.

This project aims to build a unified platform that collects, processes, validates, and visualizes marine biodiversity observation data.

The initial implementation focuses on integrating data from:

- GBIF (Global Biodiversity Information Facility)
- OBIS (Ocean Biodiversity Information System)

## 2. Objectives

- Collect marine biodiversity observation data from public APIs.
- Standardize observation records using Darwin Core concepts.
- Validate and deduplicate collected records.
- Store observation data in PostgreSQL with PostGIS.
- Provide REST APIs using FastAPI.
- Visualize geographic observation records using React and Leaflet.
- Document data provenance and basic data quality information.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Data Validation | Pydantic |
| ORM | SQLAlchemy |
| Geospatial Processing | GeoAlchemy2, PostGIS |
| Database | PostgreSQL |
| External API Integration | HTTPX |
| Frontend | React, TypeScript |
| Map Visualization | Leaflet |
| Testing | pytest |
| Containerization | Docker, Docker Compose |

## 4. Architecture

The platform follows a data pipeline architecture:

1. Data Collection
2. Data Standardization
3. Data Validation and Deduplication
4. Geospatial Database Storage
5. REST API
6. Interactive Map Visualization

## 5. Project Structure

```text
marine-biodiversity-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── etl/
│   ├── tests/
│   └── requirements.txt
├── frontend/
├── database/
├── README.md
└── DEVELOPMENT_LOG.md
```

## 6. Project Status

Currently in the initial development stage.

- [x] Development environment setup
- [x] Initial project structure
- [ ] FastAPI application initialization
- [ ] PostgreSQL and PostGIS integration
- [ ] GBIF and OBIS data integration
- [ ] Data standardization and validation
- [ ] REST API implementation
- [ ] Interactive map visualization
- [ ] Automated testing
- [ ] Docker Compose configuration

## 7. Data Sources

- GBIF: https://www.gbif.org/
- OBIS: https://obis.org/

## 8. License

To be determined.