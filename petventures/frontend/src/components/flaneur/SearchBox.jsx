import { useEffect, useRef, useState } from 'react'
import { classifyOsm } from '../../utils/waypointTypes'

// Token-free geocoder built for autocomplete.
const PHOTON = 'https://photon.komoot.io/api'
const COORD_RE = /^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$/

function label(props) {
  const bits = [props.name, props.street, props.city, props.state, props.country]
  return [...new Set(bits.filter(Boolean))].join(', ')
}

/**
 * SearchBox — overlays the map. Type a place name (Photon) or raw "lat, lng".
 * Picking a result calls onPick({ lng, lat, type, name }).
 */
export default function SearchBox({ onPick }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const boxRef = useRef(null)
  const acRef = useRef(null)

  // Close on outside click.
  useEffect(() => {
    const onDoc = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  // Debounced geocode.
  useEffect(() => {
    const coord = q.match(COORD_RE)
    if (coord) {
      setResults([])
      setOpen(false)
      return
    }
    if (q.trim().length < 3) {
      setResults([])
      return
    }
    const t = setTimeout(async () => {
      acRef.current?.abort()
      acRef.current = new AbortController()
      setLoading(true)
      try {
        const res = await fetch(`${PHOTON}?q=${encodeURIComponent(q)}&limit=5`, {
          signal: acRef.current.signal,
        })
        const data = await res.json()
        setResults(data.features || [])
        setOpen(true)
      } catch {
        /* aborted or offline — ignore */
      } finally {
        setLoading(false)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [q])

  function pickFeature(f) {
    const [lng, lat] = f.geometry.coordinates
    onPick({
      lng,
      lat,
      type: classifyOsm(f.properties.osm_key, f.properties.osm_value),
      name: label(f.properties) || 'Searched location',
    })
    setQ('')
    setResults([])
    setOpen(false)
  }

  function submit(e) {
    e.preventDefault()
    const coord = q.match(COORD_RE)
    if (coord) {
      const lat = parseFloat(coord[1])
      const lng = parseFloat(coord[2])
      onPick({ lng, lat, type: 'place', name: `${lat.toFixed(4)}, ${lng.toFixed(4)}` })
      setQ('')
      return
    }
    if (results[0]) pickFeature(results[0])
  }

  return (
    <div ref={boxRef} className="absolute left-3 top-3 z-10 w-[min(20rem,calc(100%-1.5rem))]">
      <form onSubmit={submit} className="relative">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
          placeholder="Search a place or paste lat, lng…"
          className="w-full rounded-full border-2 border-ink bg-white px-4 py-2.5 pr-10 text-sm font-medium text-ink shadow-[3px_3px_0_0_var(--color-ink)] placeholder:text-ink/40 focus:border-tang focus:outline-none"
        />
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink/50">
          {loading ? '…' : '🔍'}
        </span>
      </form>

      {open && results.length > 0 && (
        <ul className="mt-2 overflow-hidden rounded-[var(--radius-soft)] border-2 border-ink bg-white shadow-[3px_3px_0_0_var(--color-ink)]">
          {results.map((f, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => pickFeature(f)}
                className="block w-full px-4 py-2.5 text-left text-sm text-ink hover:bg-cream"
              >
                <span className="font-display font-extrabold">{f.properties.name}</span>
                <span className="block truncate text-xs text-ink/50">{label(f.properties)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
