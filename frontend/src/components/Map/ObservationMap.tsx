import { useEffect, useRef } from 'react'
import type { CircleMarker as LeafletCircleMarker } from 'leaflet'

import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'

import type { Observation } from '../../types/observation'

import 'leaflet/dist/leaflet.css'
import './ObservationMap.css'

interface ObservationMapProps {
  observations: Observation[]
  selectedObservation: Observation | null
}

interface MapSelectionControllerProps {
  selectedObservation: Observation | null
  markerRefs: {
    current: Map<number, LeafletCircleMarker>
  }
}

function MapSelectionController({
  selectedObservation,
  markerRefs,
}: MapSelectionControllerProps) {
  const map = useMap()

  useEffect(() => {
    if (
      !selectedObservation ||
      selectedObservation.latitude === null ||
      selectedObservation.longitude === null
    ) {
      return
    }

    const position: [number, number] = [
      selectedObservation.latitude,
      selectedObservation.longitude,
    ]

    map.flyTo(position, Math.max(map.getZoom(), 5), {
      duration: 1,
    })

    const marker = markerRefs.current.get(selectedObservation.id)

    marker?.openPopup()
  }, [selectedObservation, map, markerRefs])

  return null
}

function ObservationMap({
  observations,
  selectedObservation,
}: ObservationMapProps) {
  const markerRefs = useRef<Map<number, LeafletCircleMarker>>(
    new Map(),
  )

  const mappedObservations = observations.filter(
    (
      observation,
    ): observation is Observation & {
      latitude: number
      longitude: number
    } =>
      observation.latitude !== null &&
      observation.longitude !== null,
  )

  return (
    <MapContainer
      center={[0, 0]}
      zoom={2}
      scrollWheelZoom={false}
      className="observation-map"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapSelectionController
        selectedObservation={selectedObservation}
        markerRefs={markerRefs}
      />

      {mappedObservations.map((observation) => {
        const markerColor =
          observation.source === 'GBIF' ? '#2670ae' : '#18845e'

        const isSelected =
          selectedObservation?.id === observation.id

        return (
          <CircleMarker
            key={observation.id}
            ref={(marker) => {
              if (marker) {
                markerRefs.current.set(observation.id, marker)
              } else {
                markerRefs.current.delete(observation.id)
              }
            }}
            center={[
              observation.latitude,
              observation.longitude,
            ]}
            radius={isSelected ? 11 : 7}
            pathOptions={{
              color: markerColor,
              fillColor: markerColor,
              fillOpacity: isSelected ? 1 : 0.75,
              weight: isSelected ? 4 : 2,
            }}
          >
            <Popup>
              <div className="map-popup">
                <strong>{observation.scientific_name}</strong>

                <span>Source: {observation.source}</span>

                <span>
                  Date: {observation.event_date ?? 'Unknown'}
                </span>

                <span>
                  Coordinates:{' '}
                  {observation.latitude.toFixed(4)},{' '}
                  {observation.longitude.toFixed(4)}
                </span>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}

export default ObservationMap