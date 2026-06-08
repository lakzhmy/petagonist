import { useCallback, useState } from 'react'

let _seq = 0
const nextId = () =>
  (typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `wp_${Date.now()}_${_seq++}`)

/**
 * useMapWaypoints — shared waypoint state for the map + the list.
 * A waypoint is { id, lng, lat }; its number is just its index + 1.
 */
export function useMapWaypoints(max = 10) {
  const [waypoints, setWaypoints] = useState([])

  const add = useCallback(
    (lng, lat, meta = {}) =>
      setWaypoints((w) =>
        w.length >= max
          ? w
          : [
              ...w,
              { id: nextId(), lng, lat, type: meta.type || 'place', name: meta.name || null },
            ]
      ),
    [max]
  )

  const remove = useCallback(
    (id) => setWaypoints((w) => w.filter((p) => p.id !== id)),
    []
  )

  const move = useCallback(
    (fromIndex, toIndex) =>
      setWaypoints((w) => {
        if (toIndex < 0 || toIndex >= w.length) return w
        const next = w.slice()
        const [item] = next.splice(fromIndex, 1)
        next.splice(toIndex, 0, item)
        return next
      }),
    []
  )

  const clear = useCallback(() => setWaypoints([]), [])

  return { waypoints, add, remove, move, clear, max, atMax: waypoints.length >= max }
}
