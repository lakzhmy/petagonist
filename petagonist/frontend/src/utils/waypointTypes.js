/**
 * Waypoint place-types. Detected from the vector basemap on map-click, or from
 * the geocoder's osm_key/osm_value on search. Drives the list icon today and
 * (later) the contextual click animation + per-panel comic theming.
 */
export const WAYPOINT_TYPES = {
  park: { label: 'Park', icon: '🌳', tone: 'lime' },
  water: { label: 'Waterside', icon: '💧', tone: 'sky' },
  plaza: { label: 'Plaza', icon: '🕊️', tone: 'sun' },
  building: { label: 'Building', icon: '🏛️', tone: 'bubble' },
  street: { label: 'Street', icon: '🚶', tone: 'grape' },
  place: { label: 'Stop', icon: '📍', tone: 'grape' },
}

export const getType = (type) => WAYPOINT_TYPES[type] || WAYPOINT_TYPES.place

/**
 * Emoji that burst out of the click point, themed by place type — the playful
 * "this is a park!" / "this is water!" feedback when you drop a stop.
 */
export const BURST_ICONS = {
  park: ['🍃', '🐦', '🌿', '🌳', '🍂'],
  water: ['💧', '🌊', '💦', '🐟', '💧'],
  plaza: ['🕊️', '✨', '🕊️', '🥖', '✨'],
  building: ['✨', '🏛️', '🪟', '⭐', '✨'],
  street: ['🚶', '💨', '🍂', '🛵', '✨'],
  place: ['✨', '⭐', '💫', '✨', '⭐'],
}

export const getBurst = (type) => BURST_ICONS[type] || BURST_ICONS.place

/**
 * Classify raw MapLibre features (from queryRenderedFeatures) into one of our
 * types. Tuned to the OpenMapTiles schema that OpenFreeMap serves.
 * Priority: water > park > plaza > street > building.
 *
 * Notes:
 *  - Sidewalks (highway=footway/path) are plain `transportation` → street, NOT
 *    plaza. Only pedestrian zones (class=pedestrian) or named squares are plaza.
 *  - A beach (landcover=sand) reads as waterside.
 */
export function classifyFeatures(features) {
  const RANK = { water: 0, park: 1, plaza: 2, street: 3, building: 4 }
  let best = null
  let bestRank = 99
  for (const f of features || []) {
    const sl = (f.sourceLayer || '').toLowerCase()
    const cls = (f.properties?.class ?? '').toLowerCase()
    const sub = (f.properties?.subclass ?? '').toLowerCase()
    let t = null
    if (sl === 'water' || sl === 'waterway' || sl === 'ocean') t = 'water'
    else if (sl === 'landcover' && cls === 'sand') t = 'water' // beach → waterside
    else if (sl === 'landcover') t = 'park' // grass / wood / forest
    else if (sl === 'landuse' && /park|garden|recreation|cemetery|pitch|allotment|meadow|forest|grass/.test(`${cls} ${sub}`))
      t = 'park'
    else if (cls === 'pedestrian' || /plaza|square/.test(sub)) t = 'plaza'
    else if (sl.startsWith('transportation')) t = 'street'
    else if (sl === 'building') t = 'building'

    if (t && RANK[t] < bestRank) {
      best = t
      bestRank = RANK[t]
    }
  }
  return best || 'place'
}

/** Map a geocoder result's osm_key/osm_value to our type. */
export function classifyOsm(key = '', value = '') {
  const k = key.toLowerCase()
  const v = value.toLowerCase()
  if (k === 'natural' && /water|bay|beach|spring|strait/.test(v)) return 'water'
  if (k === 'water' || k === 'waterway') return 'water'
  if (k === 'leisure' && /park|garden|nature_reserve|recreation|pitch|common/.test(v)) return 'park'
  if (k === 'natural' && /wood|forest|grass|scrub|heath/.test(v)) return 'park'
  if (k === 'landuse' && /forest|grass|meadow|recreation|cemetery/.test(v)) return 'park'
  if (k === 'highway' && /pedestrian|footway|living_street|path/.test(v)) return 'plaza'
  if (k === 'place' && /square/.test(v)) return 'plaza'
  if (k === 'highway') return 'street'
  if (k === 'building') return 'building'
  return 'place'
}
