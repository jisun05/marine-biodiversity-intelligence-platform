export interface Observation {
  id: number

  source: 'GBIF' | 'OBIS'
  source_record_id: string

  scientific_name: string
  taxon_id: string | null

  basis_of_record: string | null
  event_date: string | null

  latitude: number | null
  longitude: number | null

  coordinate_uncertainty_m: number | null
  country_code: string | null

  dataset_id: string | null
}

export interface ObservationListResponse {
  total: number
  items: Observation[]
}

export interface ObservationStatistics {
  total_observations: number
  gbif_records: number
  obis_records: number
}