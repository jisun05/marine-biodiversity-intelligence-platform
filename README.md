# Marine Biodiversity Intelligence Platform

An open-source platform for integrating, standardizing, exploring, and visualizing marine biodiversity observations.

![System Architecture](docs/images/system-architecture.png)

## 1. Overview

Marine biodiversity observations are distributed across multiple international databases, each with different data structures, identifiers, and taxonomic representations.

The Marine Biodiversity Intelligence Platform addresses this fragmentation by providing a unified data integration and visualization pipeline.

The current implementation focuses on:

- Collecting marine biodiversity observations from GBIF and OBIS.
- Transforming source-specific records into a common observation model.
- Preventing duplicate records using source-based identifiers.
- Storing observation and geospatial data in PostgreSQL with PostGIS.
- Connecting observations with taxonomic information through WoRMS.
- Exposing biodiversity data through REST APIs.
- Exploring observation records through an interactive map interface.

## 2. Dataset Overview

The current MVP database contains the following records:

| Metric | Value |
|---|---:|
| Canonical observations | 30,037 |
| GBIF raw records | 15,020 |
| OBIS raw records | 15,020 |
| Persisted taxonomic entities | 15 |
| Observation-level taxonomy mappings | 208 |

**Data interpretation note:**

Raw records and canonical observations represent different stages of the data pipeline. Their counts are therefore reported separately.

The 15 persisted taxonomic entities and 208 observation-level taxonomy mappings represent a separately processed subset of the observation dataset, not the complete collection of 30,037 canonical observations.

## 3. Key Features

### 3.1 Biodiversity Data Integration

Integration of two major international biodiversity data providers:

- **GBIF** — Global Biodiversity Information Facility
- **OBIS** — Ocean Biodiversity Information System

Source-specific ingestion services collect marine biodiversity observations while preserving their original records.

### 3.2 Data Standardization

Heterogeneous source records are transformed into a unified observation model.

The pipeline includes:

- Source-specific data transformation.
- Observation validation.
- Consistent representation of observation records.
- Duplicate prevention using source and source-record identifiers.
- Batch processing for efficient database insertion.

### 3.3 Taxonomic Integration

Integration with **WoRMS (World Register of Marine Species)** for taxonomic resolution.

Implemented backend capabilities include:

- Taxonomic name resolution.
- AphiaID-based taxon identification.
- Persistent taxonomic entity storage.
- Observation-level taxonomy relationships.
- Reuse of existing taxonomic records.
- Duplicate mapping prevention.

**Current implementation status:**

Taxonomic integration and persistence are implemented and tested at the backend level. The current frontend also provides a taxonomic filter, but it covers only the subset of observations with persisted taxonomy mappings.

Improving taxonomy coverage and refining the user interface to communicate the distinction between total observations and taxonomy-mapped observations are planned for future development.

### 3.4 Geospatial Visualization

Interactive exploration of marine biodiversity observations through a React and Leaflet-based map interface.

The frontend provides:

- Observation statistics.
- Geographic observation visualization.
- Data-source filtering.
- Scientific-name search.
- Observation pagination.
- Taxonomic filtering for records with available taxonomy mappings.

### 3.5 REST API

FastAPI provides endpoints for:

- Health checks.
- Observation data retrieval.
- Data collection management.
- Taxonomic information retrieval.

Interactive API documentation is available through Swagger UI and ReDoc.

## 4. Architecture

The platform follows a modular data integration architecture.

The pipeline collects records from GBIF and OBIS, stores source-specific raw records, transforms them into a unified observation model, and makes the resulting data available through REST APIs and an interactive frontend.

Taxonomic information is resolved and persisted through a separate WoRMS integration layer.

```text
        Biodiversity Data Providers
                    |
            +-------+-------+
            |               |
           GBIF            OBIS
            |               |
            v               v
      GBIF Ingestion   OBIS Ingestion
            |               |
            v               v
       Raw GBIF         Raw OBIS
        Records          Records
            |               |
            +-------+-------+
                    |
                    v
          Data Transformation
                    |
                    v
       Unified Observation Model
                    |
                    v
          PostgreSQL + PostGIS
                    |
            +-------+-------+
            |               |
            v               v
          FastAPI      WoRMS Integration
            |               |
            |         Taxonomic Data
            |          Persistence
            |
            v
       React Frontend
            |
            v
      Leaflet Map Interface
```

## 5. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| Database | PostgreSQL 16 |
| Geospatial Database | PostGIS 3.4 |
| Geospatial ORM | GeoAlchemy2 |
| External API Communication | HTTPX |
| Frontend | React 19 |
| Programming Language | TypeScript 6 |
| Build Tool | Vite |
| HTTP Client | Axios |
| Map Visualization | Leaflet, React-Leaflet |
| Containerization | Docker, Docker Compose |
| Testing | Pytest |
| Taxonomic Data | WoRMS |

## 6. Project Structure

```text
marine-biodiversity-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── data_collection_routes.py
│   │   │   ├── health.py
│   │   │   ├── observation_routes.py
│   │   │   └── taxonomy_routes.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   │   ├── data_collection.py
│   │   │   ├── gbif_raw_observation.py
│   │   │   ├── obis_raw_observation.py
│   │   │   ├── observation.py
│   │   │   ├── observation_taxonomy.py
│   │   │   └── taxon.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── data_collection_schemas.py
│   │   │   ├── observation_schemas.py
│   │   │   └── taxonomy_schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── batch_processor.py
│   │   │   ├── data_collection_service.py
│   │   │   ├── gbif_ingestion.py
│   │   │   ├── gbif_service.py
│   │   │   ├── gbif_transformer.py
│   │   │   ├── obis_ingestion.py
│   │   │   ├── obis_service.py
│   │   │   ├── obis_transformer.py
│   │   │   ├── taxonomy_persistence_service.py
│   │   │   └── worms_service.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_batch_processor.py
│   │   ├── test_data_collection_service.py
│   │   ├── test_gbif_ingestion.py
│   │   ├── test_gbif_service.py
│   │   ├── test_gbif_transformer.py
│   │   ├── test_obis_ingestion.py
│   │   ├── test_obis_service.py
│   │   ├── test_obis_transformer.py
│   │   ├── test_observation_api.py
│   │   ├── test_taxonomy_persistence_service.py
│   │   └── test_worms_service.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   │
│   ├── src/
│   │   ├── api/
│   │   │   └── observationApi.ts
│   │   │
│   │   ├── components/
│   │   │   └── Map/
│   │   │       ├── ObservationMap.css
│   │   │       └── ObservationMap.tsx
│   │   │
│   │   ├── types/
│   │   │   ├── observation.ts
│   │   │   └── taxonomy.ts
│   │   │
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   │
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── eslint.config.js
│   └── .gitignore
│
├── scripts/
│   ├── check_worms_names.py
│   ├── dry_run_taxonomy_mapping.py
│   ├── investigate_unmatched_taxa.py
│   └── persist_taxonomy_mapping.py
│
├── docs/
│   └── images/
│       └── system-architecture.png
│
├── compose.yaml
├── .env.example
├── DEVELOPMENT_LOG.md
└── README.md
```

## 7. Data Sources

### GBIF

**Global Biodiversity Information Facility**

Provides access to global biodiversity occurrence data.

Website: https://www.gbif.org/

### OBIS

**Ocean Biodiversity Information System**

Provides access to marine biodiversity occurrence data.

Website: https://obis.org/

### WoRMS

**World Register of Marine Species**

Provides taxonomic information and marine species name resolution services.

Website: https://www.marinespecies.org/

These services provide the occurrence and taxonomic information integrated by the platform.

## 8. Testing

The project includes automated backend tests covering:

- GBIF ingestion and transformation.
- OBIS ingestion and transformation.
- Observation API.
- Data collection services.
- Batch processing.
- WoRMS integration.
- Taxonomy persistence.
- Duplicate prevention.

Run the test suite from the project root:

```bash
PYTHONPATH=. pytest backend/tests/ -v
```

The current backend test suite has **65 passing tests**.

## 9. Local Development

### Prerequisites

- Python 3.12
- Node.js and npm
- Docker and Docker Compose
- Git

### 9.1 Clone the Repository

```bash
git clone https://github.com/jisun05/marine-biodiversity-intelligence-platform.git

cd marine-biodiversity-intelligence-platform
```

### 9.2 Configure Environment Variables

Create a local environment file:

```bash
cp .env.example .env
```

Update the database credentials in `.env` as required.

### 9.3 Start PostgreSQL and PostGIS

```bash
docker compose up -d db
```

Check the database container:

```bash
docker compose ps
```

### 9.4 Install Backend Dependencies

Create and activate a virtual environment:

```bash
python -m venv .venv

source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the backend from the project root:

```bash
uvicorn backend.app.main:app --reload
```

The API documentation is available at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

The backend database connection must be configured to match the local PostgreSQL settings.

### 9.5 Install Frontend Dependencies

Open another terminal:

```bash
cd frontend

npm install
```

Start the development server:

```bash
npm run dev
```

Build the frontend:

```bash
npm run build
```

## 10. Future Improvements

Potential future development directions include:

- Expanded taxonomic coverage across the complete observation dataset.
- Improved taxonomy filtering and user interface clarity.
- Enhanced spatial filtering and geographic analysis.
- Additional biodiversity data provider integrations.
- Advanced biodiversity statistics and research-oriented visualizations.
- Improved data quality assessment and provenance tracking.
- Automated and scheduled data synchronization.

