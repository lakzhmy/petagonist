import { useCallback, useState } from 'react'

let _seq = 0
const nextId = () =>
  (typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `wp_${Date.now()}_${_seq++}`)

/**
 * useMapWaypoints — shared waypoint state for the map + the list.
 * A waypoint is { id, lng, lat, type, name, photos, selectedPhoto }.
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
              {
                id: nextId(), lng, lat,
                type: meta.type || 'place',
                name: meta.name || null,
                photos: null,
                selectedPhoto: null,
              },
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

  const setPhotos = useCallback(
    (id, photos) =>
      setWaypoints((w) =>
        w.map((wp) => (wp.id === id ? { ...wp, photos, selectedPhoto: photos?.[0] ?? null } : wp))
      ),
    []
  )

  const selectPhoto = useCallback(
    (wpId, photo) =>
      setWaypoints((w) =>
        w.map((wp) => (wp.id === wpId ? { ...wp, selectedPhoto: photo } : wp))
      ),
    []
  )

  const clear = useCallback(() => setWaypoints([]), [])

  return { waypoints, add, remove, move, setPhotos, selectPhoto, clear, max, atMax: waypoints.length >= max }
}
