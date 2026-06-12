/**
 * Tiny fetch wrapper for the Petagonist backend.
 * Calls are relative — the Vite dev server proxies /api and /static to :8000.
 */

async function handle(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      /* non-JSON error body — keep the generic message */
    }
    throw new Error(detail)
  }
  return res.json()
}

/**
 * Upload a pet photo and/or description (either is enough).
 * Returns { pet_id, image_url, description }.
 */
export async function uploadPet(file, description) {
  const form = new FormData()
  if (file) form.append('image', file)
  form.append('description', description ?? '')
  const res = await fetch('/api/pet/upload', { method: 'POST', body: form })
  return handle(res)
}

/** Generate character variants for an uploaded pet. Returns { pet_id, variants }. */
export async function generateVariants(petId) {
  const res = await fetch(`/api/pet/${petId}/generate-variants`, { method: 'POST' })
  return handle(res)
}

/**
 * Stream variant generation via SSE. Calls onVariant(variant, index, total)
 * for each variant as it finishes. Returns a promise that resolves when done.
 */
export function streamVariants(petId, { onStart, onVariant, onDone, onError }) {
  const ctrl = new AbortController()

  fetch(`/api/pet/${petId}/generate-variants-stream`, {
    method: 'POST',
    signal: ctrl.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const msg = JSON.parse(line.slice(6))

          if (msg.type === 'start') onStart?.(msg.total)
          else if (msg.type === 'variant') onVariant?.(msg.variant, msg.index, msg.total)
          else if (msg.type === 'done') onDone?.()
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError?.(err)
    })

  return () => ctrl.abort()
}

/**
 * Stream additional variants (appended to existing). Same SSE pattern as streamVariants.
 */
export function streamMoreVariants(petId, { onStart, onVariant, onDone, onError }) {
  const ctrl = new AbortController()

  fetch(`/api/pet/${petId}/generate-more-stream`, {
    method: 'POST',
    signal: ctrl.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const msg = JSON.parse(line.slice(6))

          if (msg.type === 'start') onStart?.(msg.total)
          else if (msg.type === 'variant') onVariant?.(msg.variant, msg.index, msg.total)
          else if (msg.type === 'done') onDone?.()
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError?.(err)
    })

  return () => ctrl.abort()
}

/**
 * Regenerate a single variant. Returns { variant }.
 */
export async function regenerateVariant(petId, oldVariantId, posePrompt = '') {
  const res = await fetch(`/api/pet/${petId}/regenerate-variant?old_variant_id=${encodeURIComponent(oldVariantId)}&pose_prompt=${encodeURIComponent(posePrompt)}`, {
    method: 'POST',
  })
  return handle(res)
}

/**
 * Generate the comic strip.
 * payload: { pet_id, selected_variant_ids, waypoints: [{lat,lng,order,type,name}] }
 * Returns { comic_id, panels, strip_url, pdf_url }.
 */
export async function generateComic(payload) {
  const res = await fetch('/api/flaneur/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handle(res)
}

/**
 * Stream comic panel generation via SSE. Calls onPanel(panel, index, total)
 * for each panel as it finishes. Returns an abort function.
 */
export function streamComic(payload, { onStart, onPanel, onDone, onError }) {
  const ctrl = new AbortController()

  fetch('/api/flaneur/generate-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: ctrl.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const msg = JSON.parse(line.slice(6))

          if (msg.type === 'start') onStart?.(msg.comic_id, msg.total)
          else if (msg.type === 'panel') onPanel?.(msg.panel, msg.index, msg.total)
          else if (msg.type === 'done') onDone?.()
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError?.(err)
    })

  return () => ctrl.abort()
}

/**
 * Re-roll a single panel (new scene + pose for that stop).
 * Returns the updated panel { order, image_url, location_name, type }.
 */
export async function regeneratePanel({ comic_id, order }) {
  const res = await fetch('/api/flaneur/regenerate-panel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ comic_id, order }),
  })
  return handle(res)
}

/**
 * Render a printable template for a generated comic.
 * args: { comic_id, template: 'strip'|'zine', format?: 'pdf'|'png', captions?: {idx: text} }
 * Returns { url }.
 */
export async function exportComic({ comic_id, template, format = 'pdf', captions = {} }) {
  const res = await fetch('/api/flaneur/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ comic_id, template, format, captions }),
  })
  return handle(res)
}
