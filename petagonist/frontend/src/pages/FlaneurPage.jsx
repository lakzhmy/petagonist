import { Fragment, useState } from 'react'
import PageWrapper from '../components/layout/PageWrapper'
import Tag from '../components/ui/Tag'
import PetUploader from '../components/shared/PetUploader'
import PetGallery from '../components/shared/PetGallery'
import LoadingOverlay from '../components/shared/LoadingOverlay'
import MapWithWaypoints from '../components/flaneur/MapWithWaypoints'
import WaypointList from '../components/flaneur/WaypointList'
import ComicStrip from '../components/flaneur/ComicStrip'
import { useMapWaypoints } from '../hooks/useMapWaypoints'
import { uploadPet, generateVariants, generateComic } from '../lib/api'

/**
 * FlaneurPage — the Petagonist experience and the app's home (root route).
 * The 3-step spine: Your Pet → The Route → The Comic.
 * Slice 2 wires Step 1 (upload + character gallery). Steps 2–3 are placeholders.
 */
const STEPS = [
  { n: 1, title: 'Your Pet', tone: 'tang' },
  { n: 2, title: 'The Route', tone: 'grape' },
  { n: 3, title: 'The Comic', tone: 'lime' },
]

export default function FlaneurPage() {
  const [step, setStep] = useState(1)
  const [pet, setPet] = useState(null) // { id, imageUrl, description }
  const [variants, setVariants] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [comic, setComic] = useState(null)
  const wp = useMapWaypoints(8)

  async function handleGenerate({ file, description }) {
    setLoading(true)
    setError('')
    try {
      const up = await uploadPet(file, description)
      const res = await generateVariants(up.pet_id)
      setPet({ id: up.pet_id, imageUrl: up.image_url, description: up.description })
      setVariants(res.variants)
      setSelectedIds([])
    } catch (e) {
      setError(e.message || 'Something went wrong generating characters.')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegenerate() {
    if (!pet) return
    setLoading(true)
    setError('')
    try {
      const res = await generateVariants(pet.id)
      setVariants(res.variants)
      setSelectedIds([])
    } catch (e) {
      setError(e.message || 'Could not regenerate characters.')
    } finally {
      setLoading(false)
    }
  }

  function toggleVariant(id) {
    setSelectedIds((cur) =>
      cur.includes(id) ? cur.filter((x) => x !== id) : cur.length < 5 ? [...cur, id] : cur
    )
  }

  async function handleGenerateComic() {
    setStep(3)
    setComic(null)
    setLoading(true)
    setError('')
    try {
      const res = await generateComic({
        pet_id: pet.id,
        selected_variant_ids: selectedIds,
        waypoints: wp.waypoints.map((w, i) => ({
          lat: w.lat,
          lng: w.lng,
          order: i,
          type: w.type,
          name: w.name,
        })),
      })
      setComic(res)
    } catch (e) {
      setError(e.message || 'Could not generate the comic.')
    } finally {
      setLoading(false)
    }
  }

  function handleRestart() {
    setComic(null)
    setVariants([])
    setSelectedIds([])
    setPet(null)
    wp.clear()
    setError('')
    setStep(1)
  }

  // Return to the upload screen (Step 1) to swap the pet, keeping the route.
  function backToUpload() {
    setVariants([])
    setSelectedIds([])
    setPet(null)
    setError('')
    setStep(1)
  }

  const goToStep = (n) => n <= step && setStep(n)

  return (
    <PageWrapper surface="grape">
      <LoadingOverlay show={loading} />

      <section className="mx-auto max-w-5xl px-5 py-12">
        <div className="text-center">
          <h1 className="mx-auto max-w-2xl font-display text-4xl font-black leading-tight text-white sm:text-5xl">
            Let&apos;s make an awesome pet adventure for your baby!
          </h1>
        </div>

        {/* Stepper */}
        <ol className="mx-auto mt-10 flex max-w-xl items-start justify-between">
          {STEPS.map((s, i) => {
            const reached = s.n <= step
            return (
              <Fragment key={s.n}>
                <li className="flex w-20 flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={() => goToStep(s.n)}
                    disabled={!reached}
                    className={`spring ${reached ? 'cursor-pointer hover:scale-110' : 'cursor-default'}`}
                  >
                    <Tag
                      tone={reached ? s.tone : 'cream'}
                      className={`h-11 w-11 justify-center !rounded-full text-lg ${reached ? '' : 'opacity-60'}`}
                    >
                      {s.n < step ? '✓' : s.n}
                    </Tag>
                  </button>
                  <span className={`font-display text-sm font-extrabold ${reached ? 'text-white' : 'text-white/50'}`}>
                    {s.title}
                  </span>
                </li>
                {i < STEPS.length - 1 && (
                  <span
                    className={`mt-5 h-1 flex-1 rounded-full ${s.n < step ? 'bg-sun' : 'bg-white/20'}`}
                  />
                )}
              </Fragment>
            )
          })}
        </ol>

        {error && (
          <p className="mt-6 text-center font-display font-bold text-sun">{error}</p>
        )}

        {/* ---- Step body ---- */}
        <div className="mt-10">
          {/* Back affordance for the later steps (the stepper also navigates). */}
          {step > 1 && (
            <button
              type="button"
              onClick={() => goToStep(step - 1)}
              className="spring mb-5 font-display text-sm font-extrabold text-white/70 hover:text-white"
            >
              ← Back
            </button>
          )}

          {step === 1 &&
            (variants.length === 0 ? (
              <PetUploader onSubmit={handleGenerate} loading={loading} />
            ) : (
              <PetGallery
                variants={variants}
                selectedIds={selectedIds}
                onToggle={toggleVariant}
                onRegenerate={handleRegenerate}
                onContinue={() => setStep(2)}
                onBack={backToUpload}
              />
            ))}

          {step === 2 && (
            <div className="grid gap-5 lg:grid-cols-3">
              <div className="pv-frame h-[420px] overflow-hidden lg:col-span-2 lg:h-[560px]">
                <MapWithWaypoints
                  waypoints={wp.waypoints}
                  onAdd={wp.add}
                  onRemove={wp.remove}
                  atMax={wp.atMax}
                />
              </div>
              <div className="lg:h-[560px]">
                <WaypointList
                  waypoints={wp.waypoints}
                  max={wp.max}
                  onRemove={wp.remove}
                  onMove={wp.move}
                  onGenerate={handleGenerateComic}
                />
              </div>
            </div>
          )}
          {step === 3 &&
            (comic ? (
              <ComicStrip comic={comic} onRestart={handleRestart} />
            ) : (
              !error && (
                <div className="rounded-[var(--radius-card)] border-2 border-dashed border-white/30 bg-white/5 p-14 text-center">
                  <span className="animate-bob inline-block text-6xl">📖</span>
                  <p className="mt-4 font-display text-xl font-black text-white">
                    Drawing your comic…
                  </p>
                </div>
              )
            ))}
        </div>
      </section>
    </PageWrapper>
  )
}
