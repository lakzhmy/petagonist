/**
 * Tiny fetch wrapper for the Petventures backend.
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

/** Upload a pet photo + description. Returns { pet_id, image_url, description }. */
export async function uploadPet(file, description) {
  const form = new FormData()
  form.append('image', file)
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
