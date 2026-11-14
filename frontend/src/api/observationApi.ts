import axios from 'axios'

import type {
  ObservationListResponse,
  ObservationStatistics,
} from '../types/observation'

import type {
  TaxonListResponse,
} from '../types/taxonomy'

const apiClient = axios.create({
  baseURL: '/api',
})

interface ObservationParams extends PaginationParams {
  source?: 'GBIF' | 'OBIS'
  scientific_name?: string
}

interface TaxonParams extends PaginationParams {
  search?: string
  rank?: string
}

interface PaginationParams {
  skip?: number
  limit?: number
}

export const getObservations = async (
  params?: ObservationParams,
): Promise<ObservationListResponse> => {
  const response = await apiClient.get<ObservationListResponse>(
    '/observations',
    { params },
  )

  return response.data
}

export const getObservationStatistics = async (): Promise<ObservationStatistics> => {
  const response = await apiClient.get<ObservationStatistics>(
    '/observations/statistics',
  )

  return response.data
}

export const getTaxa = async (
  params?: TaxonParams,
): Promise<TaxonListResponse> => {
  const response = await apiClient.get<TaxonListResponse>(
    '/taxa',
    { params },
  )

  return response.data
}

export const getTaxonObservations = async (
  aphiaId: number,
  params?: PaginationParams,
): Promise<ObservationListResponse> => {
  const response = await apiClient.get<ObservationListResponse>(
    `/taxa/${aphiaId}/observations`,
    { params },
  )

  return response.data
}