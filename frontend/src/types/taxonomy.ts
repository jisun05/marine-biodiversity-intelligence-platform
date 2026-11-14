export interface Taxon {
  aphia_id: number
  canonical_name: string
  authority: string | null
  taxonomic_rank: string
  parent_aphia_id: number | null
  observation_count: number
}

export interface TaxonListResponse {
  total: number
  items: Taxon[]
}
