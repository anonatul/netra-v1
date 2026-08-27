import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { MapData } from '../api'

const OPENFREEMAP_STYLE = 'https://tiles.openfreemap.org/styles/fiord'

// Fallback: dark tactical grid when tiles are unreachable (offline demo, NFR-096)
const FALLBACK_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  name: 'netra-grid',
  sources: {
    grid: {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: graticule(19.0, 72.8) },
    },
  },
  layers: [
    { id: 'bg', type: 'background', paint: { 'background-color': '#10171e' } },
    {
      id: 'grid-lines',
      type: 'line',
      source: 'grid',
      paint: { 'line-color': '#2b3740', 'line-width': 1 },
    },
  ],
}

// static lat/lon lines so the fallback reads as a tactical grid, not a blank screen
function graticule(lat: number, lon: number): Array<{
  type: 'Feature'
  properties: Record<string, never>
  geometry: { type: 'LineString'; coordinates: number[][] }
}> {
  const features: ReturnType<typeof graticule> = []
  for (let i = -12; i <= 12; i++) {
    const l = lon + i * 0.02
    features.push({
      type: 'Feature',
      properties: {},
      geometry: { type: 'LineString', coordinates: [[l, lat - 0.3], [l, lat + 0.3]] },
    })
  }
  for (let i = -12; i <= 12; i++) {
    const a = lat + i * 0.02
    features.push({
      type: 'Feature',
      properties: {},
      geometry: { type: 'LineString', coordinates: [[lon - 0.3, a], [lon + 0.3, a]] },
    })
  }
  return features
}

const PRIORITY_COLOR: Record<string, string> = {
  P1: '#ef4444',
  P2: '#f97316',
  P3: '#eab308',
  P4: '#94a3b8',
  UNRATED: '#64748b',
}

export default function NetraMap({
  data,
  selectedId,
  onSelect,
}: {
  data: MapData | null
  selectedId: string | null
  onSelect: (id: string | null) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const selectedRef = useRef(selectedId)
  selectedRef.current = selectedId
  const fellBackRef = useRef(false)

  useEffect(() => {
    if (!containerRef.current) return
    const container = containerRef.current
    const map = new maplibregl.Map({
      container,
      style: OPENFREEMAP_STYLE,
      center: [72.8777, 19.076],
      zoom: 12,
    })
    mapRef.current = map

    const fallback = () => {
      if (fellBackRef.current) return
      fellBackRef.current = true
      try {
        map.setStyle(FALLBACK_STYLE)
      } catch {
        /* already set */
      }
    }

    // tile fetch / style load failures -> offline dark grid (connectivity state)
    map.on('error', fallback)
    // some environments fail to load the style without emitting an error; catch that too
    const styleTimeout = window.setTimeout(() => {
      if (!map.isStyleLoaded()) fallback()
    }, 12000)

    map.on('load', () => {
      map.addSource('heat', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'heat-layer',
        type: 'heatmap',
        source: 'heat',
        paint: {
          'heatmap-weight': 1,
          'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 11, 1.5, 15, 3],
          'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 11, 18, 15, 40],
          'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(76, 113, 126, 0)',
            0.3, 'rgba(76, 113, 126, 0.5)',
            0.6, 'rgba(193, 158, 91, 0.65)',
            0.85, 'rgba(190, 102, 77, 0.78)',
            1, 'rgba(164, 70, 57, 0.9)',
          ],
          'heatmap-opacity': 0.55,
        },
      })
      map.addSource('zones', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'zone-fill',
        type: 'fill',
        source: 'zones',
        paint: {
          'fill-color': ['match', ['get', 'priority'], 'P1', '#ef4444', 'P2', '#f97316', 'P3', '#eab308', '#64748b'],
          'fill-opacity': 0.22,
        },
      })
      map.addLayer({
        id: 'zone-line',
        type: 'line',
        source: 'zones',
        paint: {
          'line-color': ['match', ['get', 'priority'], 'P1', '#ef4444', 'P2', '#f97316', 'P3', '#eab308', '#64748b'],
          'line-width': 2,
          'line-dasharray': [2, 2],
        },
      })
      map.addSource('incidents', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: 'incident-dot',
        type: 'circle',
        source: 'incidents',
        paint: {
          'circle-radius': 7,
          'circle-color': ['match', ['get', 'priority'], 'P1', '#ef4444', 'P2', '#f97316', 'P3', '#eab308', '#64748b'],
          'circle-stroke-color': '#e5e1d7',
          'circle-stroke-width': 1.5,
        },
      })

      map.on('click', 'incident-dot', (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features?.[0]) {
          const id = String(e.features[0].properties?.incident_id)
          onSelect(id)
          map.easeTo({ center: (e.lngLat as { lng: number; lat: number }), zoom: 14 })
        }
      })
      map.on('click', (e: maplibregl.MapMouseEvent) => {
        const features = map.queryRenderedFeatures(e.point)
        if (!features.some((f) => f.source === 'incidents' || f.source === 'zones')) {
          onSelect(null)
        }
      })
    })

    const onResize = () => map.resize()
    window.addEventListener('resize', onResize)

    return () => {
      window.clearTimeout(styleTimeout)
      window.removeEventListener('resize', onResize)
      map.remove()
      mapRef.current = null
    }
  }, [onSelect])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return
    if (!map.getSource('heat')) return

    const heatFeatures = (data?.heat_points ?? [])
      .filter((p) => !p.flagged)
      .map((p) => ({
        type: 'Feature' as const,
        properties: {},
        geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] },
      }))
    ;(map.getSource('heat') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: heatFeatures,
    })

    const zoneFeatures = (data?.zones ?? []).map((z) => ({
      type: 'Feature' as const,
      properties: { priority: z.priority, zone_id: z.zone_id },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [
          circlePolygon(z.lat, z.lon, z.radius_m).map(([la, lo]) => [lo, la]),
        ],
      },
    }))
    ;(map.getSource('zones') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: zoneFeatures,
    })

    const incidentFeatures = (data?.incidents ?? [])
      .filter((i) => i.lat !== null && i.lon !== null)
      .map((i) => ({
        type: 'Feature' as const,
        properties: {
          incident_id: i.incident_id,
          priority: i.priority,
          severity: i.severity,
          victims: i.victim_estimate,
          evidence: i.evidence_count,
        },
        geometry: { type: 'Point' as const, coordinates: [i.lon as number, i.lat as number] },
      }))
    ;(map.getSource('incidents') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: incidentFeatures,
    })

    const selected = selectedRef.current
    if (selected && data) {
      const inc = data.incidents.find((i) => i.incident_id === selected)
      if (inc?.lat !== null && inc?.lon !== undefined) {
        const layer = map.getLayer('incident-dot')
        if (layer) {
          map.setPaintProperty('incident-dot', 'circle-stroke-color', [
            'case',
            ['==', ['get', 'incident_id'], selected],
            '#c47458',
            '#ffffff',
          ])
        }
      }
    }
  }, [data])

  const located = data?.incidents.filter((incident) => incident.lat !== null && incident.lon !== null).length ?? 0
  const zones = data?.zones.length ?? 0

  return (
    <div className="absolute inset-0 h-full w-full">
      <div ref={containerRef} className="absolute inset-0 h-full w-full" />
      <div className="netra-map-head" aria-hidden="true">
        <div>
          <span className="netra-map-kicker">Live field coverage</span>
          <strong>Operational map</strong>
        </div>
        <span className="netra-map-sync">AUTO · 4 SEC</span>
      </div>
      <div className="netra-map-footer" aria-hidden="true">
        <div className="netra-map-legend">
          <span><i className="netra-map-dot netra-dot-p1" />P1 critical</span>
          <span><i className="netra-map-dot netra-dot-p2" />P2 urgent</span>
          <span><i className="netra-map-dot netra-dot-p3" />P3 monitored</span>
        </div>
        <div className="netra-map-counts">
          <span><b>{located}</b> located incidents</span>
          <span><b>{zones}</b> active zones</span>
        </div>
      </div>
    </div>
  )
}

function circlePolygon(lat: number, lon: number, radiusM: number): Array<[number, number]> {
  const points: Array<[number, number]> = []
  const dLat = radiusM / 111320
  const dLon = radiusM / (111320 * Math.cos((lat * Math.PI) / 180))
  for (let i = 0; i < 48; i++) {
    const a = (i / 48) * 2 * Math.PI
    points.push([lat + dLat * Math.sin(a), lon + dLon * Math.cos(a)])
  }
  return points
}

export { PRIORITY_COLOR }