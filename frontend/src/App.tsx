import { useEffect, useState } from 'react'
import ObservationMap from './components/Map/ObservationMap'

import {
  getObservations,
  getObservationStatistics,
  getTaxa,
  getTaxonObservations,
} from './api/observationApi'

import type { Taxon } from './types/taxonomy'

import type {
  Observation,
  ObservationListResponse,
  ObservationStatistics,
} from './types/observation'

import './App.css'

type SourceFilter = 'ALL' | 'GBIF' | 'OBIS'

function App() {

  const [result, setResult] =
    useState<ObservationListResponse | null>(null)

  const [statistics, setStatistics] =
    useState<ObservationStatistics | null>(null)

  const [statisticsLoading, setStatisticsLoading] = useState(true)


  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedObservation, setSelectedObservation] =
    useState<Observation | null>(null)


  const [source, setSource] = useState<SourceFilter>('ALL')
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [pageSize, setPageSize] = useState(15)
  const [currentPage, setCurrentPage] = useState(1)

  const [selectedTaxon, setSelectedTaxon] =
    useState<Taxon | null>(null)

  const [taxa, setTaxa] = useState<Taxon[]>([])
  const [taxaLoading, setTaxaLoading] = useState(true)


  useEffect(() => {
    if (!selectedObservation) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedObservation(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedObservation]);

  // Fetch global observation statistics
  useEffect(() => {
    let cancelled = false

    const fetchStatistics = async () => {
      try {
        const data = await getObservationStatistics()

        if (!cancelled) {
          setStatistics(data)
        }
      } catch {
        console.error('Unable to load observation statistics.')
      } finally {
        if (!cancelled) {
          setStatisticsLoading(false)
        }
      }
    }

    fetchStatistics()

    return () => {
      cancelled = true
    }
  }, [])

  // Fetch available taxa for the taxonomy filter
  useEffect(() => {
    const fetchTaxa = async () => {
      try {
        const data = await getTaxa({ limit: 100 })
        setTaxa(data.items)
      } catch {
        console.error('Unable to load taxonomy data.')
      } finally {
        setTaxaLoading(false)
      }
    }

    fetchTaxa()
  }, [])

  // Fetch observations when filters change
  useEffect(() => {
    let cancelled = false

    const fetchObservations = async () => {
      setLoading(true)
      setError(null)

      try {
        const params = {
          skip: (currentPage - 1) * pageSize,
          limit: pageSize,
        }

        const data = selectedTaxon
          ? await getTaxonObservations(selectedTaxon.aphia_id, params)
          : await getObservations({
            ...(source !== 'ALL' ? { source } : {}),
            ...(searchQuery
              ? { scientific_name: searchQuery }
              : {}),
            ...params,
          })

        if (!cancelled) {
          setResult(data)
        }
      } catch {
        if (!cancelled) {
          setError(
            'Unable to load observation data. Please check the API server.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchObservations()

    return () => {
      cancelled = true
    }
  }, [source, searchQuery, currentPage, pageSize, selectedTaxon])



  const observations: Observation[] = result?.items ?? []

  const totalRecords = result?.total ?? 0
  const totalPages = Math.ceil(totalRecords / pageSize)

  const startRecord =
    totalRecords === 0 ? 0 : (currentPage - 1) * pageSize + 1

  const endRecord = Math.min(
    currentPage * pageSize,
    totalRecords,
  )

  const getPageNumbers = (): (number | '...')[] => {
    if (totalPages <= 5) {
      return Array.from(
        { length: totalPages },
        (_, index) => index + 1,
      )
    }

    let start = Math.max(2, currentPage - 1)
    let end = Math.min(totalPages - 1, currentPage + 1)

    if (currentPage <= 2) {
      end = 3
    }

    if (currentPage >= totalPages - 1) {
      start = totalPages - 2
    }

    const pages: (number | '...')[] = [1]

    if (start > 2) {
      pages.push('...')
    }

    for (let page = start; page <= end; page++) {
      pages.push(page)
    }

    if (end < totalPages - 1) {
      pages.push('...')
    }

    pages.push(totalPages)

    return pages
  }

  // Submit scientific name search
  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSelectedObservation(null);
    setCurrentPage(1)
    setSearchQuery(searchInput);
  };

  // Select or deselect an observation
  const handleObservationClick = (observation: Observation) => {
    setSelectedObservation((current) =>
      current?.id === observation.id ? null : observation,
    )

  }

  return (
    <main className="app-container">
      {/* Header */}
      <header className="top-header">
        <div className="brand">
          <div className="brand-icon">M</div>

          <div>
            <h1>Marine Biodiversity</h1>
            <span>INTELLIGENCE PLATFORM</span>
          </div>
        </div>

        <div className="header-status">
          <span className="status-dot" />
          Data platform
        </div>
      </header>

      <section className="dashboard">
        {/* Page Heading */}
        <div className="page-heading">
          <div>
            <span className="eyebrow">MARINE RESEARCH DATA</span>
            <h2>Biodiversity Overview</h2>
            <p>
              Explore marine species observations from global
              biodiversity databases.
            </p>
          </div>
        </div>

        {/* Summary Cards */}
        <section className="summary-grid">
          <article className="summary-card total-card">
            <span className="card-label">TOTAL OBSERVATIONS</span>

            <strong>
              {statisticsLoading
                ? '—'
                : statistics?.total_observations.toLocaleString() ?? '—'}
            </strong>

            <span className="card-description">
              All records in database
            </span>
          </article>

          <article className="summary-card">
            <span className="card-label">GBIF RECORDS</span>

            <strong>
              {statisticsLoading
                ? '—'
                : statistics?.gbif_records.toLocaleString() ?? '—'}
            </strong>

            <span className="card-description">
              Global Biodiversity Information Facility
            </span>
          </article>

          <article className="summary-card">
            <span className="card-label">OBIS RECORDS</span>

            <strong>
              {statisticsLoading
                ? '—'
                : statistics?.obis_records.toLocaleString() ?? '—'}
            </strong>

            <span className="card-description">
              Ocean Biodiversity Information System
            </span>
          </article>
        </section>

        <div className="filter-panel">
          <form
            onSubmit={handleSearch}
            className="search-form"
          >
            <input
              type="text"
              placeholder="Search scientific name..."
              value={searchInput}
              onChange={(event) =>
                setSearchInput(event.target.value)
              }
            />

            <button type="submit">Search</button>
          </form>

          <select
            value={source}
            onChange={(event) => {
              setSelectedObservation(null);
              setCurrentPage(1)
              setSource(event.target.value as SourceFilter);
            }}
          >
            <option value="ALL">All sources</option>
            <option value="GBIF">GBIF</option>
            <option value="OBIS">OBIS</option>
          </select>

          <select
            value={selectedTaxon?.aphia_id ?? 'ALL'}
            onChange={(event) => {
              const value = event.target.value

              setSelectedObservation(null)
              setCurrentPage(1)

              if (value === 'ALL') {
                setSelectedTaxon(null)
              } else {
                const taxon = taxa.find(
                  (item) => item.aphia_id === Number(value),
                )

                setSelectedTaxon(taxon ?? null)
                setSearchInput('')
                setSearchQuery('')
              }
            }}
            disabled={taxaLoading}
            aria-label="Filter by taxon"
          >
            <option value="ALL">
              {taxaLoading ? 'Loading taxa...' : 'All taxa'}
            </option>

            {taxa.map((taxon) => (
              <option
                key={taxon.aphia_id}
                value={taxon.aphia_id}
              >
                {taxon.canonical_name} ({taxon.observation_count})
              </option>
            ))}
          </select>


        </div>
        {/* Main Observation Explorer */}
        <section className="explorer-layout">

          {/* Left: Observation List */}
          <section className="content-section observation-list-section">
            <div className="section-heading">
              <div>
                <h3>Observation Records</h3>
                <p>
                  Select a record to explore its details.
                </p>
              </div>

              <label className="page-size-control">
                <span>Show</span>

                <select
                  value={pageSize}
                  onChange={(event) => {
                    setSelectedObservation(null)
                    setCurrentPage(1)
                    setPageSize(Number(event.target.value))
                  }}
                >
                  <option value={15}>15</option>
                  <option value={30}>30</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </label>
            </div>

            {/* Search and Source Filter */}


            {error && (
              <div className="error-message">{error}</div>
            )}

            {/* Accordion Observation List */}
            <div className="observation-list">
              {loading ? (
                <p className="empty-message">
                  Loading observation data...
                </p>
              ) : observations.length === 0 ? (
                <p className="empty-message">
                  No observations found.
                </p>
              ) : (
                observations.map((observation) => {
                  const isSelected =
                    selectedObservation?.id === observation.id

                  return (
                    <article
                      key={observation.id}
                      className={`observation-item ${isSelected ? 'selected' : ''
                        }`}
                    >
                      {/* Accordion Header */}
                      <button
                        type="button"
                        className="observation-item-header"
                        aria-expanded={isSelected}
                        onClick={() =>
                          handleObservationClick(observation)
                        }
                      >
                        <span
                          className="observation-item-id"
                          title={`Internal Observation ID: ${observation.id}`}
                        >
                          {observation.id}
                        </span>

                        <span className="observation-item-name">
                          {observation.scientific_name}
                        </span>

                        <span
                          className={`source-badge ${observation.source.toLowerCase()}`}
                        >
                          {observation.source}
                        </span>

                        <span className="accordion-indicator">
                          {isSelected ? '−' : '+'}
                        </span>
                      </button>

                      {/* Expanded Observation Details */}
                      {isSelected && (
                        <div className="observation-item-details">

                          <div className="detail-item">
                            <span className="detail-label">
                              SCIENTIFIC NAME
                            </span>
                            <span className="detail-value">
                              {observation.scientific_name}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              SOURCE
                            </span>
                            <span className="detail-value">
                              {observation.source}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              SOURCE RECORD ID
                            </span>
                            <span className="detail-value">
                              {observation.source_record_id}
                            </span>

                            <a
                              className="source-record-link"
                              href={
                                observation.source === 'GBIF'
                                  ? `https://www.gbif.org/occurrence/${encodeURIComponent(
                                    observation.source_record_id,
                                  )}`
                                  : `https://obis.org/occurrence/${encodeURIComponent(
                                    observation.source_record_id,
                                  )}`
                              }
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              View original record on{' '}
                              {observation.source} ↗
                            </a>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              OBSERVATION DATE
                            </span>
                            <span className="detail-value">
                              {observation.event_date ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              LATITUDE
                            </span>
                            <span className="detail-value">
                              {observation.latitude?.toFixed(6) ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              LONGITUDE
                            </span>
                            <span className="detail-value">
                              {observation.longitude?.toFixed(6) ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              COUNTRY CODE
                            </span>
                            <span className="detail-value">
                              {observation.country_code ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              DATASET ID
                            </span>
                            <span className="detail-value">
                              {observation.dataset_id ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              TAXON ID
                            </span>
                            <span className="detail-value">
                              {observation.taxon_id ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              BASIS OF RECORD
                            </span>
                            <span className="detail-value">
                              {observation.basis_of_record ?? '—'}
                            </span>
                          </div>

                          <div className="detail-item">
                            <span className="detail-label">
                              COORDINATE UNCERTAINTY
                            </span>
                            <span className="detail-value">
                              {observation.coordinate_uncertainty_m !== null
                                ? `${observation.coordinate_uncertainty_m} m`
                                : '—'}
                            </span>
                          </div>

                        </div>
                      )}
                    </article>
                  )
                })
              )}
            </div>
            {/* Pagination */}
            {!loading && totalRecords > 0 && (
              <div className="pagination">
                <span className="pagination-info">
                  Showing {startRecord}–{endRecord} of {totalRecords} records
                </span>

                <div className="pagination-controls">
                  <button
                    type="button"
                    className="pagination-arrow"
                    aria-label="Previous page"
                    onClick={() => {
                      setSelectedObservation(null)
                      setCurrentPage((page) => page - 1)
                    }}
                    disabled={currentPage === 1}
                  >
                    ◀
                  </button>

                  <div className="pagination-pages">
                    {getPageNumbers().map((page, index) =>
                      page === '...' ? (
                        <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                          ...
                        </span>
                      ) : (
                        <button
                          key={page}
                          type="button"
                          className={`pagination-number ${currentPage === page ? 'active' : ''
                            }`}
                          aria-label={`Go to page ${page}`}
                          aria-current={currentPage === page ? 'page' : undefined}
                          onClick={() => {
                            setSelectedObservation(null)
                            setCurrentPage(page)
                          }}
                        >
                          {page}
                        </button>
                      ),
                    )}
                  </div>

                  <button
                    type="button"
                    className="pagination-arrow"
                    aria-label="Next page"
                    onClick={() => {
                      setSelectedObservation(null)
                      setCurrentPage((page) => page + 1)
                    }}
                    disabled={currentPage >= totalPages}
                  >
                    ▶
                  </button>
                </div>
              </div>
            )}



          </section>

          {/* Right: Observation Map */}
          <section className="map-preview">
            <div>
              <span className="eyebrow">
                GEOGRAPHIC DISTRIBUTION
              </span>

              <h3>Observation Map</h3>

              <p>
                Explore the geographical distribution of marine
                biodiversity observations.
              </p>
            </div>

            <div className="map-container">
              <ObservationMap
                observations={observations}
                selectedObservation={selectedObservation}
              />
            </div>

            <div className="map-legend">
              <span>
                <i className="legend-dot gbif-dot" />
                GBIF
              </span>

              <span>
                <i className="legend-dot obis-dot" />
                OBIS
              </span>
            </div>
          </section>

        </section>
      </section>
    </main>
  )
}

export default App
