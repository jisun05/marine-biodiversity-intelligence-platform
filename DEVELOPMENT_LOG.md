# Development Log

## 1-1 Development Environment and Project Initialization

### Completed

- Configured WSL2 with Ubuntu.

- Installed Python 3.12.16 using pyenv.

- Created a project-specific Python virtual environment.

- Configured VS Code with WSL integration.

- Configured Docker Desktop and WSL integration.

- Initialized the project directory structure.

### Technical Decisions

**Python 3.12**

Selected Python 3.12 to provide a stable development environment and compatibility with the project's Python dependencies.

**WSL2 Ubuntu**

Selected WSL2 to develop in a Linux environment while using Windows and VS Code as the primary desktop environment.

**Docker Desktop**

Selected Docker Desktop for local container management and reproducible development environments.

### Next Steps

- Initialize the FastAPI application.

- Implement the initial health check endpoint.

- Document the API using OpenAPI and Swagger UI.

## 1-2. Database Models and API Schema Design

### 1. Database Architecture Design

Designed a hybrid Raw + Canonical data architecture to integrate marine biodiversity observations from GBIF and OBIS.

The two data sources have different data structures and may provide different fields. Using a single table for all original records could result in many source-specific nullable columns and make the data model difficult to maintain.

To address this, I decided to separate raw data storage from the canonical observation model.

**Architecture:**

- `gbif_raw_observations`: Stores original GBIF API records.

- `obis_raw_observations`: Stores original OBIS API records.

- `observations`: Stores normalized records using a common data structure.

The raw tables preserve source-specific information in PostgreSQL JSONB columns, while the canonical table contains only common fields required by the application's business logic and API.

**Design considerations:**

- Preserve original source data for traceability and future reprocessing.

- Avoid unnecessary source-specific columns in the canonical table.

- Provide a consistent data structure for the API and frontend.

- Allow GBIF and OBIS records to be processed through a shared business logic layer.

**Trade-offs:**

This architecture requires additional storage and transformation logic. However, it provides better separation of concerns and makes it easier to integrate additional biodiversity data sources in the future.

### 2. SQLAlchemy Database Models

Implemented three SQLAlchemy ORM models.

**Observation (Canonical Model)**

Created a common observation model containing:

- Source and source record identifier

- Scientific name and taxonomic identifier

- Basis of record and event date

- Latitude and longitude

- Coordinate uncertainty

- Country code and dataset identifier

Optional fields were configured to accept NULL values because not all biodiversity records contain complete information.

Added a composite UNIQUE constraint on `(source, source_record_id)` to prevent duplicate canonical records while allowing different data sources to use the same source record identifier.

**GBIFRawObservation and OBISRawObservation**

Created separate raw data models for GBIF and OBIS.

Both models contain:

- Internal database identifier

- Source record identifier with a UNIQUE constraint

- Original API response stored as JSONB

- Data ingestion timestamp

Used PostgreSQL JSONB to preserve the structured source payload and support future data inspection and processing.

### 3. SQLAlchemy Model Registration and Validation

Registered all three ORM models through the models package.

Verified that SQLAlchemy correctly registered the following tables in `Base.metadata`:

- `observations`

- `gbif_raw_observations`

- `obis_raw_observations`

Inspected the generated table metadata to verify:

- Column names and data types

- NULL constraints

- Primary keys

- UNIQUE constraints

- JSONB column definitions

Corrected a column name mismatch during the composite UNIQUE constraint configuration and successfully verified the final constraint.

### 4. Pydantic API Schemas

Implemented Pydantic response schemas in `observation_schemas.py`.

**ObservationResponse**

Defines the response structure for a single biodiversity observation.

Used `ConfigDict(from_attributes=True)` to allow Pydantic to read attributes directly from SQLAlchemy ORM objects.

**ObservationListResponse**

Defines the response structure for multiple observations using:

- `total`: Number of observations returned.

- `items`: A list of `ObservationResponse` objects.

This provides a consistent response format for records originating from different data sources.

### 5. Validation and Testing

Performed initial validation using Python command-line tests without connecting to a database.

Successfully verified:

- SQLAlchemy ORM object to Pydantic model conversion.

- JSON serialization of observation records.

- Date serialization into ISO 8601 format.

- Handling of nullable fields.

- Serialization of multiple observations from different sources in a single response.

Tested both GBIF and OBIS example records to confirm that they can be represented using the same API response schema.

### 6. Current Development Status

**Completed:**

- Initial FastAPI application setup.

- Health check endpoint.

- SQLAlchemy declarative base.

- Canonical observation model.

- GBIF and OBIS raw data models.

- Composite UNIQUE constraint for canonical observations.

- Pydantic observation response schemas.

- Initial model and schema validation.

**Next Steps:**

- Configure PostgreSQL with PostGIS using Docker Compose.

- Implement SQLAlchemy database connection and session management.

- Create database tables.

- Test actual database insertion and retrieval.

- Begin implementation of GBIF and OBIS data ingestion.

## 2-1. Frontend Dashboard and Interactive Map Integration

### 1. Interactive Map Integration

Integrated the previously implemented `ObservationMap` component into the main React dashboard (`App.tsx`).

**Implementation:**

- Imported the `ObservationMap` component into `App.tsx`.

- Replaced the static map placeholder with the interactive map.

- Passed observation records from the dashboard to the map component through React props.

- Added a map legend to distinguish between GBIF and OBIS observation records.

- Added CSS styling for the map container and legend.

The map now receives observation data from the dashboard and renders geographic markers based on the available latitude and longitude values.

### 2. Map Visualization and Interaction

Verified the map rendering and marker interactions in the browser.

**Implemented features:**

- OpenStreetMap tile layer.

- Geographic observation markers using React-Leaflet.

- Blue markers for GBIF observations.

- Green markers for OBIS observations.

- Interactive popups displaying observation details.

Each marker popup displays:

- Scientific name

- Data source

- Observation date

- Geographic coordinates

Confirmed that marker clicks successfully open the corresponding observation popups.

### 3. JSX Syntax Error Resolution

Encountered a TypeScript compilation error during frontend integration:

`TS17008: JSX element 'section' has no corresponding closing tag.`

**Cause:**

The outer `dashboard` section in `App.tsx` was missing its closing JSX tag.

**Resolution:**

Added the missing `</section>` tag to properly close the nested dashboard structure.

### 4. Frontend Build Verification

Executed the frontend validation commands:

```bash

npm run lint

npm run build

```

**Build result:**

- ESLint: Passed.

- TypeScript compilation: Passed.

- Vite production build: Passed.

- Modules transformed: 120.

The production build completed successfully.

### 5. Technical Decisions

**Component Separation**

Kept map rendering logic inside the dedicated `ObservationMap` component instead of placing it directly in `App.tsx`.

This separates data retrieval and dashboard state management from geographic visualization.

**Props-Based Data Passing**

Used React props to pass observation records from the dashboard to the map component.

This allows the map to use the same observation dataset as the dashboard without implementing a separate API request.

**Source-Based Marker Styling**

Used different marker colors to distinguish GBIF and OBIS records visually.

This provides a simple way to identify the origin of each observation during data exploration.

### 6. Development Status

**Completed:**

- Integrated the interactive map into the React dashboard.

- Connected dashboard observation data to the map component.

- Implemented GBIF and OBIS marker visualization.

- Verified marker popup interactions.

- Fixed the JSX syntax error.

- Successfully passed frontend linting and production build.

**Next Steps:**

- Test synchronization between search results and map markers.

- Verify GBIF and OBIS source filtering on the map.

- Review observations without geographic coordinates.

- Improve marker usability and map presentation.

- Perform end-to-end integration testing of the backend and frontend.

## 3-1. Observation Search and Filtering

### 1. Observation Search Implementation

Implemented observation search functionality in the frontend dashboard.

**Implemented features:**

- Added scientific name search.

- Added data source filtering for GBIF and OBIS.

- Connected search parameters to the existing observation API.

- Updated the dashboard when search criteria change.

### 2. Search and Filtering Integration

Connected the dashboard search functionality with the backend observation API.

**Implemented features:**

- Retrieved observations using the scientific name query parameter.

- Filtered observations by data source.

- Supported combined scientific name and source filtering.

- Displayed the total number of matching observations.

- Updated map markers based on the filtered observation results.

### 3. Integration Testing

Verified search and filtering behavior using the integrated GBIF and OBIS datasets.

**Test results:**

- All observations: 30 records.

- GBIF observations: 15 records.

- OBIS observations: 15 records.

- Delphinus delphis search: 20 records.

- Thunnus albacares search: 10 records.

- Combined species and source filtering.

- Non-existent species search returning zero results.

Confirmed that the map visualization correctly reflects the filtered observation records.

---

## 3-2. Observation Detail and Map Interaction

### 1. Observation Detail Modal

Implemented a detail modal to display individual observation records.

**Implemented features:**

- Added clickable observation IDs to the observation table.

- Displayed detailed information for the selected observation.

- Used React Portal to render the modal through `document.body`.

- Added an overlay click interaction to close the modal.

- Added a close button.

- Implemented Escape key handling to close the modal.

The detail view includes:

- Observation ID

- Scientific name

- Data source

- Source record ID

- Observation date

- Geographic coordinates

- Country code

- Dataset ID

- Coordinate uncertainty

- Taxonomic identifier

- Basis of record

### 2. Map and Detail Synchronization

Connected the selected observation state with the interactive map.

**Implemented features:**

- Passed the selected observation from the dashboard to the map component through React props.

- Used React Leaflet's `useMap()` hook to access the Leaflet map instance.

- Used `useRef()` to maintain references to individual map markers.

- Used `map.flyTo()` to navigate to the selected observation's geographic coordinates.

- Automatically opened the selected marker's popup.

- Highlighted the selected marker by increasing its radius and border weight.

Observations without geographic coordinates are excluded from map marker rendering.

### 3. Technical Decisions

**React State Management**

Used the selected observation state in the main dashboard to synchronize the detail view and map interaction.

**Leaflet Map Control**

Used React Leaflet hooks to control the Leaflet map instance without introducing additional API requests.

**Marker References**

Used React refs to access individual Leaflet marker instances and open their popups programmatically.

---

## 3-3. Original Data Source Traceability

### 1. Source Record Identification

Verified that the canonical observation records preserve the original record identifiers from both GBIF and OBIS.

**GBIF:**

- Uses numeric occurrence identifiers.

- Example: `6130016195`

**OBIS:**

- Uses UUID-based occurrence identifiers.

- Example: `00000d3e-1ac8-417b-8a65-7af94c50747d`

### 2. Original Record Links

Implemented source-specific external links in the observation detail modal.

**GBIF:**

- Generated occurrence URLs using the GBIF source record identifier.

- URL pattern: `https://www.gbif.org/occurrence/{source_record_id}`

**OBIS:**

- Generated occurrence URLs using the OBIS source record identifier.

- URL pattern: `https://obis.org/occurrence/{source_record_id}`

**Implemented features:**

- Generated external URLs based on the observation source.

- Displayed a link to the original record in the detail modal.

- Opened external records in a new browser tab.

- Applied `noopener noreferrer` for external link security.

### 3. Validation

Tested the external links using actual observation records.

**Validation results:**

- Verified GBIF original occurrence record access.

- Verified OBIS original occurrence record access.

- Confirmed that both source-specific links open successfully.

### 4. Technical Decisions

**Data Provenance**

Preserved the original source identifiers in the canonical observation model to maintain traceability between normalized records and their original data sources.

Generated external links dynamically using the source type and original record identifier instead of storing redundant URLs in the database.

This approach keeps the canonical data model independent of source-specific URL structures while allowing users to navigate back to the original records.

## 3-4. Marine Species Data Expansion

### 1. Multi-Source Data Collection

- Collected occurrence records for *Balaenoptera musculus* (Blue whale) from GBIF and OBIS.

- Retrieved 10 records from each data source.

- Successfully inserted 20 new raw observation records.

- Verified duplicate detection during ingestion.

### 2. Raw Data Transformation

- Transformed GBIF and OBIS raw records into the canonical observation model.

- Inserted 10 new canonical observations from each source.

- Skipped 15 existing records per source to prevent duplicate entries.

### 3. Database Verification

Verified the following database record counts:

- Canonical observations: 50 records.

- GBIF raw observations: 25 records.

- OBIS raw observations: 25 records.

- Blue whale observations: 20 records across both data sources.

Confirmed that the collected records contain valid scientific names and geographic coordinates.

---

## 3-5. Data Collection Management Foundation

### 1. DataCollection Model

- Created a new SQLAlchemy model to manage data collection jobs.

- Added fields for scientific names, data sources, trigger type, execution status, collection statistics, error messages, and timestamps.

- Separated collection job records from canonical biodiversity observations.

### 2. Database Integration

- Registered the DataCollection model in `backend/app/models/__init__.py`.

- Created the `data_collections` table in the development PostgreSQL database using SQLAlchemy metadata.

- Verified that all four database tables are registered successfully.

### 3. Pydantic Schemas

- Created `data_collection_schemas.py`.

- Implemented `DataCollectionCreate` for validating collection requests.

- Implemented `DataCollectionResponse` for returning individual collection job results.

- Implemented `DataCollectionListResponse` for returning collection job lists.

- Added validation for scientific names, supported data sources (GBIF and OBIS), and record limits (1–300).

- Verified successful schema imports.

### 4. Technical Decisions

- Selected `/api/data-collections` as the resource endpoint for managing collection jobs.

- Decided to support both individual species collection and multi-species batch processing.

- Planned to reuse existing GBIF and OBIS ingestion services and transformers.

- Excluded scheduled execution from the current MVP scope.

## 4-1. Batch Data Collection Service and Processor

### 1. Data Collection Service Implementation

Implemented a data collection service to coordinate data ingestion and transformation from multiple biodiversity data sources.

**Implemented features:**

- Integrated GBIF and OBIS ingestion services.

- Connected source-specific transformers to the data collection workflow.

- Aggregated ingestion and transformation statistics.

- Tracked successful and failed data sources independently.

- Implemented error handling to prevent one source failure from interrupting the remaining collection process.

- Added collection status classification.

**Collection statuses:**

- `completed`: All selected data sources processed successfully.

- `partial`: At least one source succeeded while another failed.

- `failed`: All selected sources failed.

### 2. Batch Processor Implementation

Created `batch_processor.py` to support collection requests involving multiple marine species.

**Implemented features:**

- Processed multiple scientific names sequentially.

- Created an independent `DataCollection` database record for each species.

- Tracked individual collection job statuses.

- Updated job status from `pending` to `running`.

- Stored fetched, inserted, and transformed record counts.

- Recorded error messages for failed collection jobs.

- Recorded collection completion timestamps.

- Continued processing subsequent species when an individual collection job failed.

### 3. Testing

Created `test_data_collection_service.py` and `test_batch_processor.py`.

**Test scenarios:**

- Successful collection from GBIF and OBIS.

- Partial collection when one data source fails.

- Successful processing of multiple species.

- Independent collection job creation.

- Continuation of batch processing after an individual species fails.

All four tests passed.

### 4. Technical Decisions

**Independent Collection Jobs**

Designed each species collection as an independent database record rather than storing the entire batch as a single job.

This allows individual species collection results, execution statuses, and errors to be tracked separately.

**Sequential Batch Processing**

Implemented sequential processing for the MVP to keep the workflow simple and predictable.

Parallel processing and background task execution were excluded from the current scope.

**Error Isolation**

Handled collection failures at the individual source and species levels to prevent a single failure from terminating the entire batch.

---

## 4-2. Data Collection REST API Implementation

### 1. Data Collection API Router

Created `data_collection_routes.py` to expose batch data collection functionality through FastAPI.

Implemented the following endpoints:

| Method | Endpoint | Description |

|---|---|---|

| POST | `/data-collections` | Execute batch data collection for multiple species |

| GET | `/data-collections` | Retrieve collection job records |

| GET | `/data-collections/{collection_id}` | Retrieve an individual collection job |

### 2. Batch Collection Endpoint

Implemented the POST endpoint using the existing `DataCollectionCreate` Pydantic schema.

**Supported request parameters:**

- `scientific_names`: List of scientific names to collect.

- `sources`: Selected data sources (GBIF and OBIS).

- `limit`: Maximum number of records per species and source.

Connected the endpoint to the batch processor and returned individual collection results.

### 3. Collection Job Retrieval

Implemented collection job retrieval endpoints.

**Collection List:**

- Retrieves collection jobs from the database.

- Returns the total number of matching jobs.

- Supports pagination using `skip` and `limit`.

- Orders records by creation time in descending order.

**Individual Collection:**

- Retrieves a collection job using its database identifier.

- Returns HTTP 404 when the requested job does not exist.

### 4. FastAPI Integration

Registered the new data collection router in `main.py`.

Verified the registered API paths through the generated OpenAPI specification.

Successfully confirmed the availability of:

- `/health`

- `/observations`

- `/data-collections`

- `/data-collections/{collection_id}`

### 5. Real API Integration Testing

Executed an actual batch collection request through Swagger UI.

Tested the collection of:

- `Megaptera novaeangliae`

- `Carcharodon carcharias`

Both GBIF and OBIS APIs were used as data sources.

Verified that collection job records were created and that ingestion and transformation statistics were returned through the REST API.

---

## 4-3. OBIS Date Normalization and Raw Data Reprocessing

### 1. Data Format Inconsistency Identification

Identified a date parsing issue during real-world integration testing with the OBIS API.

The OBIS API returned an event date in the following format:

`11/11/2019`

The existing transformer only supported ISO 8601 date strings, causing the transformation process to fail.

**Error encountered:**

`Invalid isoformat string: '11/11/2019'`

### 2. Date Normalization Implementation

Updated `obis_transformer.py` to support multiple date formats.

Implemented the `parse_obis_event_date()` function.

**Supported formats:**

- ISO 8601 date: `2019-11-11`

- ISO 8601 datetime: `2019-11-11T12:30:00`

- OBIS date format: `DD/MM/YYYY`

Invalid or unsupported date values return `None` instead of interrupting the transformation process.

### 3. Data Type Consistency Fix

Identified and removed a redundant date conversion operation.

The date parsing function already returned Python `date` objects, but the transformer attempted to process the returned object as a string.

Removed the unnecessary conversion to ensure consistent data types throughout the transformation pipeline.

### 4. Unit Testing

Extended `test_obis_transformer.py` with additional date parsing tests.

**Test scenarios:**

- ISO 8601 date parsing.

- OBIS slash-separated date parsing.

- Invalid date handling.

All five OBIS transformer tests passed.

### 5. Raw Data Reprocessing

Re-executed the collection workflow for `Megaptera novaeangliae` after fixing the date parsing issue.

The original OBIS raw records had already been stored in PostgreSQL before the initial transformation failure.

Instead of downloading the records again, the existing raw data was reused for transformation.

**Reprocessing results:**

- Total fetched: 20

- Total inserted: 0

- Total transformed: 10

- Collection status: `completed`

- Error message: `null`

Successfully transformed the previously unprocessed OBIS records without inserting duplicate raw records.

### 6. Technical Decisions

**Raw Data Preservation and Reprocessing**

Maintained the separation between source-specific raw records and canonical observations.

This allowed failed transformation operations to be retried independently without repeating external API data ingestion.

**Date Normalization**

Implemented source-specific date normalization to handle differences between external biodiversity data providers.

### 7. Backend Test Results

Executed the complete backend test suite.

**Test results:**

- Batch Processor: 2 passed.

- Data Collection Service: 2 passed.

- GBIF Transformer: 2 passed.

- OBIS Transformer: 5 passed.

- Observation API: 8 passed.

**Total: 19 passed, 1 warning.**

All backend tests passed successfully.

## 4-4. WoRMS Taxonomy Integration Foundation

**Implemented:**

- Investigated taxonomic inconsistencies between GBIF and OBIS records.

- Evaluated WoRMS as a common taxonomy reference.

- Verified accepted names, synonyms, taxonomic ranks, and parent taxa through the WoRMS REST API.

- Added the `Taxon` SQLAlchemy model for storing WoRMS taxonomy records.

- Added the `ObservationTaxonomy` model for linking observations to WoRMS taxa.

- Registered both models in the SQLAlchemy metadata.

- Created the `taxa` and `observation_taxonomy` tables in PostgreSQL.

- Verified that existing observation and raw data records remained unchanged.

- Implemented the initial asynchronous WoRMS API client in `worms_service.py`.

**Validation:**

- Confirmed all six application tables are registered in SQLAlchemy metadata.

- Confirmed the two new tables exist in PostgreSQL.

- Verified that existing records were preserved (210 observations, 105 GBIF raw records, and 105 OBIS raw records).

- Successfully imported the WoRMS service module.

**Next Steps:**

- Test actual WoRMS API requests.

- Implement taxonomy normalization and persistence.

- Link observations to accepted WoRMS taxa.

## 4-5. Observation-level Taxonomy Mapping Plan

### 1. Observation Data Retrieval

Extended `scripts/dry_run_taxonomy_mapping.py` to retrieve individual observation records alongside unique scientific names.

Retrieved the following fields:

- Observation ID

- Original scientific name

- Data source (GBIF / OBIS)

This allows taxonomy resolution results to be evaluated at the individual observation level rather than only at the scientific-name level.

### 2. Observation-level Taxonomy Mapping

Implemented an in-memory lookup dictionary to associate WoRMS resolution results with individual observations.

- Reused previously resolved scientific names to avoid redundant API requests.

- Mapped each observation to its corresponding WoRMS taxonomy result.

- Included AphiaID, canonical scientific name, and taxonomic rank.

- Preserved unresolved `nomen nudum` records without assigning valid AphiaIDs.

### 3. Mapping Statistics and Aggregation

Implemented observation-level statistics, including:

- Total observations and successfully mapped observations.

- Taxonomy mapping coverage.

- Observation counts grouped by AphiaID.

- Observation counts grouped by data source.

- Separate classification of `nomen nudum`, unmatched, ambiguous, and API error records.

### 4. Dry Run Results

Successfully analyzed 210 observation records using 29 unique scientific names.

**Taxonomy resolution results:**

| Metric | Result |

|---|---:|

| Total observations | 210 |

| Successfully mapped observations | 208 |

| Nomen nudum records | 2 |

| Unmatched records | 0 |

| Ambiguous records | 0 |

| API errors | 0 |

| Mapping coverage | 99.05% |

| Unique AphiaIDs | 15 |

**Taxonomic rank distribution:**

| Rank | Count |

|---|---:|

| Species | 11 |

| Subspecies | 4 |

**Data source distribution:**

| Source | Accepted | Nomen nudum | Total |

|---|---:|---:|---:|

| GBIF | 104 | 1 | 105 |

| OBIS | 104 | 1 | 105 |

### 5. Mapping Plan Validation

Performed additional validation on the generated observation-level mapping plan.

Successfully verified:

- All 210 observations were included.

- All 210 observation IDs were unique.

- 208 valid mappings contained AphiaIDs.

- No duplicate observation IDs were found.

- No valid mapping had a missing AphiaID.

All validation checks passed.

### 6. Generated Reports

Generated the following JSON reports:

- `taxonomy_dry_run_report.json`

- `taxonomy_observation_mapping_plan.json`

Both reports preserve the analysis results for further inspection and validation.

**No database modifications were performed.**

### 7. Planned Follow-up

- Review the existing taxonomy persistence implementation.

- Verify transaction handling and duplicate prevention.

- Persist the 15 unique taxa into the `taxa` table.

- Persist the 208 valid observation-taxonomy relationships.

- Exclude the two `nomen nudum` records from valid taxonomy mappings.

- Verify database records and idempotent execution.

### 8. Taxonomy Persistence Implementation and Verification

Implemented the taxonomy persistence workflow to store WoRMS taxonomy information and link accepted taxa to individual observations.

**Persistence implementation:**

- Added `taxonomy_persistence_service.py` to manage Taxon and ObservationTaxonomy records.
- Used WoRMS AphiaID to identify and reuse existing Taxon records.
- Implemented creation and updating of observation-taxonomy relationships.
- Added validation for required taxonomy fields.
- Separated transaction management from the persistence service.

**Database persistence:**

Successfully persisted the validated observation-level taxonomy mapping plan.

| Metric | Result |
|---|---:|
| Unique Taxon records | 15 |
| Observation-Taxonomy relationships | 208 |
| Unique AphiaIDs | 15 |
| Unique mapped Observation IDs | 208 |
| Excluded nomen nudum records | 2 |

Verified that the database contains 15 Taxon records and 208 ObservationTaxonomy records.

The two `nomen nudum` records were excluded from valid taxonomy mappings.

**Transaction and duplicate prevention:**

- Implemented transaction commit after successful persistence.
- Added rollback handling for persistence errors.
- Reused existing Taxon records based on AphiaID.
- Reused existing ObservationTaxonomy records based on observation ID.
- Prevented duplicate records when the same mapping is processed repeatedly.

**Automated tests:**

Added and executed persistence service tests covering:

1. Creation of new Taxon and ObservationTaxonomy records.
2. Reuse of an existing Taxon across multiple observations.
3. Updating an existing observation-taxonomy mapping.
4. Validation of missing required fields.
5. Repeated persistence of the same mapping without creating duplicates.

**Test results:**

- Total tests: 5
- Passed: 5
- Failed: 0

All taxonomy persistence service tests passed.


## 4-6. Dataset Expansion and Final MVP Verification


### 1. Dataset Expansion

Expanded the marine biodiversity dataset by adding six additional species:

- Sphyrna lewini
- Lepidochelys olivacea
- Balaenoptera acutorostrata
- Pterois volitans
- Epinephelus itajara
- Apostichopus japonicus

Verified data availability through both GBIF and OBIS APIs before ingestion.

Collected up to 500 records per species from each data source.

### 2. Ingestion and Transformation Results

Successfully processed all six species through the existing ingestion pipeline.

- Total records fetched: 6,000
- Total records inserted into raw tables: 6,000
- Total records transformed: 5,997
- All six data collection jobs completed successfully.
- No collection errors were reported.

### 3. Database Verification

Verified the final database record counts:

| Table | Records |
|---|---:|
| GBIF Raw Observations | 15,020 |
| OBIS Raw Observations | 15,020 |
| Observations | 30,037 |
| Observation Taxonomy | 208 |

The platform now contains 30,037 canonical observation records, exceeding the initial target of 30,000 records.

### 4. Code Cleanup and Repository Review

- Reviewed the codebase for duplicate and unnecessary code.
- Inspected Git staging and unstaged changes.
- Reviewed `.gitignore` configuration.
- Verified that `.env` is excluded from Git tracking.
- Reviewed `.env.example` to ensure it contains placeholder credentials only.
- Identified temporary taxonomy analysis reports for exclusion from the MVP commit.

### 5. Project Status

The platform has successfully exceeded the initial dataset target of 30,000 canonical observations.

The core data ingestion, transformation, storage, API, and frontend visualization workflows are operational.

The next steps are:

- Complete the development log.
- Finalize the Git staging area.
- Create a milestone commit.
- Prepare README documentation and application screenshots.
- Prepare the project demonstration for the Senckenberg TETTRIX application.
