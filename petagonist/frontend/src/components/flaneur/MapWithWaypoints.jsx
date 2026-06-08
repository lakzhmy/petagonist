import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import SearchBox from './SearchBox'
import { classifyFeatures, getBurst } from '../../utils/waypointTypes'

// Barcelona — the user is at IAAC.
const BARCELONA = { center: [2.1734, 41.3851], zoom: 13 }

// Token-free OpenFreeMap vector basemap. Vector tiles let us classify what's
// under a click (park / water / street …). Overridable via VITE_MAP_STYLE_URL.
const DEFAULT_STYLE = 'https://tiles.openfreemap.org/styles/liberty'

const routeGeoJSON = (waypoints) => ({
  type: 'Feature',
  geometry: { type: 'LineString', coordinates: waypoints.map((w) => [w.lng, w.lat]) },
})

/**
 * MapWithWaypoints — click the map to drop numbered pins (auto-classified by
 * place type); search a place/coords to add + fly there; route line links them.
 */
export default function MapWithWaypoints({ waypoints, onAdd, onRemove, atMax }) {
  const containerRef = useRef(null)
  const burstLayerRef = useRef(null)
  const mapRef = useRef(null)
  const readyRef = useRef(false)
  const markersRef = useRef(new Map()) // id -> { marker, el }
  // Latest values reachable from stable map handlers.
  const stateRef = useRef({ onAdd, onRemove, atMax, waypoints })
  stateRef.current = { onAdd, onRemove, atMax, waypoints }

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
          'line-opacity': 0.95,
        },
      })
      readyRef.current = true
      map.resize()
      syncMarkers()
    })

    map.on('click', (e) => {
      if (stateRef.current.atMax) return
      // Classify what's under the click from the vector tiles.
      const pad = 6
      const feats = map.queryRenderedFeatures([
        [e.point.x - pad, e.point.y - pad],
        [e.point.x + pad, e.point.y + pad],
      ])
      const type = classifyFeatures(feats)
      stateRef.current.onAdd(e.lngLat.lng, e.lngLat.lat, { type })
      spawnBurst(e.point.x, e.point.y, type)
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

    for (const [id, entry] of store) {
      if (!liveIds.has(id)) {
        entry.marker.remove()
        store.delete(id)
      }
    }

    waypoints.forEach((w, i) => {
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
        const popupNode = buildPopup(w, () => stateRef.current.onRemove(w.id))
        const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
          .setLngLat([w.lng, w.lat])
          .setPopup(new maplibregl.Popup({ offset: 24, closeButton: false }).setDOMContent(popupNode))
          .addTo(map)
        entry = { el, marker }
        store.set(w.id, entry)
      }
      entry.el.textContent = String(i + 1)
      entry.el.className = `wp-pin ${role}`.trim()
    })

    const src = map.getSource('route')
    if (src) src.setData(routeGeoJSON(waypoints))
  }

  // -- Themed click burst ---------------------------------------------------
  // Appends a ripple + a fan of emoji at (x,y) pixel; each self-removes on
  // animationend. Only uses refs, so the map handler's closure can call it.
  function spawnBurst(x, y, type) {
    const layer = burstLayerRef.current
    if (!layer) return
    const icons = getBurst(type)

    const ripple = document.createElement('div')
    ripple.className = 'pv-burst pv-ripple'
    ripple.style.left = `${x}px`
    ripple.style.top = `${y}px`
    ripple.addEventListener('animationend', () => ripple.remove())
    layer.appendChild(ripple)

    const n = icons.length
    icons.forEach((icon, i) => {
      const p = document.createElement('div')
      p.className = 'pv-burst pv-particle'
      p.textContent = icon
      p.style.left = `${x}px`
      p.style.top = `${y}px`
      // Fan upward: spread the icons across an arc centered on straight-up.
      const ang = ((-90 + (i - (n - 1) / 2) * 30) * Math.PI) / 180
      const dist = 44 + Math.random() * 28
      p.style.setProperty('--dx', `${(Math.cos(ang) * dist).toFixed(0)}px`)
      p.style.setProperty('--dy', `${(Math.sin(ang) * dist).toFixed(0)}px`)
      p.style.setProperty('--rot', `${(Math.random() * 60 - 30).toFixed(0)}deg`)
      p.style.animationDelay = `${i * 40}ms`
      p.addEventListener('animationend', () => p.remove())
      layer.appendChild(p)
    })
  }

  // -- Camera helpers -------------------------------------------------------
  function fitTo(points, { animate = true } = {}) {
    const map = mapRef.current
    if (!map || points.length === 0) return
    if (points.length === 1) {
      map.flyTo({ center: [points[0].lng, points[0].lat], zoom: 14, duration: animate ? 800 : 0 })
      return
    }
    const b = points.reduce(
      (bb, p) => bb.extend([p.lng, p.lat]),
      new maplibregl.LngLatBounds([points[0].lng, points[0].lat], [points[0].lng, points[0].lat])
    )
    map.fitBounds(b, { padding: 70, maxZoom: 15, duration: animate ? 800 : 0 })
  }

  function handlePick({ lng, lat, type, name }) {
    if (stateRef.current.atMax) return
    onAdd(lng, lat, { type, name })
    // Burst at the picked point's current screen position (before the camera moves).
    const map = mapRef.current
    if (map) {
      const pt = map.project([lng, lat])
      spawnBurst(pt.x, pt.y, type)
    }
    // Google-Maps feel: fit to all stops once there are 2+, else fly to the one.
    fitTo([...stateRef.current.waypoints, { lng, lat }])
  }

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {/* Themed click bursts render into this empty, React-owned overlay. */}
      <div ref={burstLayerRef} className="pointer-events-none absolute inset-0 z-[5] overflow-hidden" />
      <SearchBox onPick={handlePick} />
      {waypoints.length >= 2 && (
        <button
          type="button"
          onClick={() => fitTo(stateRef.current.waypoints)}
          className="spring absolute bottom-3 left-3 z-10 rounded-full border-2 border-grape-light bg-white px-4 py-2 font-display text-sm font-extrabold text-grape shadow-[var(--shadow-lift)] hover:-translate-y-0.5"
        >
          ⤢ Fit route
        </button>
      )}
    </div>
  )
}

function buildPopup(w, onRemove) {
  const node = document.createElement('div')
  node.innerHTML = `
    <div style="font-weight:700;color:#1A1A2E;margin-bottom:6px">${
      w.name ? escapeHtml(w.name) : 'Waypoint'
    }</div>
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

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
}
