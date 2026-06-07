import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

// Barcelona — the user is at IAAC.
const BARCELONA = { center: [2.1734, 41.3851], zoom: 13 }

// Token-free CARTO Voyager raster basemap (real streets, friendly colors).
// Overridable with VITE_MAP_STYLE_URL (a full MapLibre style URL).
const DEFAULT_STYLE = {
  version: 8,
  sources: {
    carto: {
      type: 'raster',
      tiles: [
        'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors © CARTO',
    },
  },
  layers: [{ id: 'carto', type: 'raster', source: 'carto' }],
}

const routeGeoJSON = (waypoints) => ({
  type: 'Feature',
  geometry: {
    type: 'LineString',
    coordinates: waypoints.map((w) => [w.lng, w.lat]),
  },
})

/**
 * MapWithWaypoints — click the map to drop numbered pins; a route line links
 * them in order; clicking a pin opens a popup with coords + Remove.
 *
 * Imperative MapLibre lives behind refs; the component reconciles markers and
 * the route line whenever the `waypoints` prop changes.
 */
export default function MapWithWaypoints({ waypoints, onAdd, onRemove, atMax }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const readyRef = useRef(false)
  const markersRef = useRef(new Map()) // id -> { marker, el }
  // Keep latest callbacks reachable from stable map handlers.
  const cbRef = useRef({ onAdd, onRemove, atMax })
  cbRef.current = { onAdd, onRemove, atMax }

  // -- Init map once --------------------------------------------------------
  useEffect(() => {
    const style = import.meta.env.VITE_MAP_STYLE_URL || DEFAULT_STYLE
    const map = new maplibregl.Map({
      container: containerRef.current,
      style,
      center: BARCELONA.center,
      zoom: BARCELONA.zoom,
      attributionControl: { compact: true },
    })
    mapRef.current = map
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      map.addSource('route', { type: 'geojson', data: routeGeoJSON([]) })
      map.addLayer({
        id: 'route-line',
        type: 'line',
        source: 'route',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#FF5C35',
          'line-width': 5,
          'line-dasharray': [1.4, 1.2],
          'line-opacity': 0.9,
        },
      })
      readyRef.current = true
      map.resize()
      syncMarkers()
    })

    map.on('click', (e) => {
      if (cbRef.current.atMax) return
      cbRef.current.onAdd(e.lngLat.lng, e.lngLat.lat)
    })

    return () => {
      map.remove()
      mapRef.current = null
      readyRef.current = false
      markersRef.current.clear()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // -- Reconcile markers + route whenever waypoints change ------------------
  useEffect(() => {
    if (readyRef.current) syncMarkers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waypoints])

  function syncMarkers() {
    const map = mapRef.current
    if (!map) return
    const store = markersRef.current
    const liveIds = new Set(waypoints.map((w) => w.id))

    // Remove markers for deleted waypoints.
    for (const [id, entry] of store) {
      if (!liveIds.has(id)) {
        entry.marker.remove()
        store.delete(id)
      }
    }

    // Add new + update numbers/colors on existing.
    waypoints.forEach((w, i) => {
      const number = i + 1
      const role =
        waypoints.length > 1 && i === 0
          ? 'wp-pin--start'
          : waypoints.length > 1 && i === waypoints.length - 1
            ? 'wp-pin--end'
            : ''
      let entry = store.get(w.id)
      if (!entry) {
        const el = document.createElement('div')
        el.className = 'wp-pin wp-pin--new'
        el.addEventListener('animationend', () => el.classList.remove('wp-pin--new'))

        const popupNode = buildPopup(w, () => cbRef.current.onRemove(w.id))
        const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
          .setLngLat([w.lng, w.lat])
          .setPopup(new maplibregl.Popup({ offset: 24, closeButton: false }).setDOMContent(popupNode))
          .addTo(map)
        entry = { el, marker }
        store.set(w.id, entry)
      }
      entry.el.textContent = String(number)
      entry.el.className = `wp-pin ${role}`.trim()
    })

    // Update the route line.
    const src = map.getSource('route')
    if (src) src.setData(routeGeoJSON(waypoints))
  }

  return <div ref={containerRef} className="h-full w-full" />
}

function buildPopup(w, onRemove) {
  const node = document.createElement('div')
  node.innerHTML = `
    <div style="font-weight:700;color:#1A1A2E;margin-bottom:6px">Waypoint</div>
    <div style="font-size:12px;color:#555;margin-bottom:8px">
      ${w.lat.toFixed(4)}, ${w.lng.toFixed(4)}
    </div>`
  const btn = document.createElement('button')
  btn.textContent = 'Remove'
  btn.style.cssText =
    'background:#FF5C35;color:#fff;border:none;border-radius:9999px;' +
    'padding:6px 14px;font-weight:800;cursor:pointer;font-family:inherit'
  btn.addEventListener('click', onRemove)
  node.appendChild(btn)
  return node
}
