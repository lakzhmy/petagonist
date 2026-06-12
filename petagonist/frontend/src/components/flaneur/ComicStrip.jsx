import { useEffect, useState } from 'react'
import Button from '../ui/Button'
import Tag from '../ui/Tag'
import Sparkle from '../ui/Sparkle'
import PanelView from './PanelView'
import { exportComic, regeneratePanel } from '../../lib/api'

// Brand colours for blank cells — mirrors backend layout.BLANK_COLORS so the
// on-screen preview matches the printed page.
const BLANK_COLORS = [
  '#FF5C35', '#4A2FBD', '#FF69B4', '#7ED957',
  '#5EC5FF', '#FFD700', '#9C8CF5', '#FF8FAB',
]
const SLOTS = 8 // both templates always lay out 8 cells

/**
 * ComicStrip — the finished output. Panels land in a 3-column grid; any unused
 * slots (fewer than 8 stops) become editable colour cells. Strip vs Zine is
 * chosen only at download, where it renders a printable 16:9 page.
 */
export default function ComicStrip({ comic, onRestart, generating, progress }) {
  const [panels, setPanels] = useState(comic?.panels ?? [])

  useEffect(() => {
    if (comic?.panels) setPanels(comic.panels)
  }, [comic?.panels?.length])

  const n = panels.length
  const [captions, setCaptions] = useState({}) // { slotIndex: text } for blanks
  const [format, setFormat] = useState('pdf')
  const [busy, setBusy] = useState('') // 'strip' | 'zine' while exporting
  const [rolling, setRolling] = useState({}) // { order: true } while re-rolling
  const [error, setError] = useState('')

  function setCaption(i, text) {
    setCaptions((c) => ({ ...c, [i]: text }))
  }

  async function regenerate(order) {
    setRolling((r) => ({ ...r, [order]: true }))
    setError('')
    try {
      const updated = await regeneratePanel({ comic_id: comic.comic_id, order })
      setPanels((ps) => ps.map((p) => (p.order === order ? updated : p)))
    } catch (e) {
      setError(e.message || 'Could not re-roll that panel.')
    } finally {
      setRolling((r) => ({ ...r, [order]: false }))
    }
  }

  async function download(template) {
    setBusy(template)
    setError('')
    try {
      const { url } = await exportComic({
        comic_id: comic.comic_id,
        template,
        format,
        captions,
      })
      const a = document.createElement('a')
      a.href = url
      a.download = `petagonist-${template}.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      setError(e.message || 'Could not build that template.')
    } finally {
      setBusy('')
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6 text-center">
        <Tag tone="sun" icon={<Sparkle size={14} twinkle />}>
          {generating ? 'Drawing your comic…' : 'Your comic is ready!'}
        </Tag>
        <h2 className="mt-2 font-display text-3xl font-black text-white">
          {generating
            ? `Drawing panel ${progress ? progress.done : 0} of ${progress ? progress.total : '…'}`
            : `A ${n}-stop adventure`}
        </h2>
        {!generating && n < SLOTS && (
          <p className="mt-2 text-sm text-white/70">
            {SLOTS - n} blank {SLOTS - n === 1 ? 'cell' : 'cells'} below — add a
            note to any of them, or leave them as colour blocks.
          </p>
        )}
      </div>

      {/* 3-column grid of 8 slots */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        {Array.from({ length: SLOTS }).map((_, i) => {
          if (i < n) {
            return (
              <PanelView
                key={panels[i].order}
                panel={panels[i]}
                index={i}
                onRegenerate={() => regenerate(panels[i].order)}
                rolling={!!rolling[panels[i].order]}
              />
            )
          }
          if (generating && i === n) {
            return (
              <div
                key="drawing-next"
                className="pv-frame flex aspect-[3/2] items-center justify-center bg-white/5"
              >
                <div className="text-center">
                  <span className="inline-block animate-bob text-4xl">🎨</span>
                  <p className="mt-2 px-3 font-display text-xs font-bold text-white/60">
                    Drawing…
                  </p>
                </div>
              </div>
            )
          }
          if (!generating) {
            return (
              <BlankCell
                key={`blank-${i}`}
                color={BLANK_COLORS[i % BLANK_COLORS.length]}
                value={captions[i] ?? ''}
                onChange={(t) => setCaption(i, t)}
              />
            )
          }
          return null
        })}
      </div>

      {error && (
        <p className="mt-6 text-center font-display font-bold text-sun">{error}</p>
      )}

      {/* Download controls — pick a layout to download */}
      <div className="mt-10 flex flex-col items-center gap-4">
        <p className="font-display text-sm font-extrabold text-white/70">
          Download as a printable page (16:9)
        </p>

        {/* Format toggle */}
        <div className="flex items-center gap-1 rounded-full bg-white/10 p-1">
          {['pdf', 'png'].map((f) => (
            <button
              key={f}
              onClick={() => setFormat(f)}
              className={`spring rounded-full px-4 py-1.5 font-display text-sm font-extrabold uppercase ${
                format === f ? 'bg-sun text-ink' : 'text-white/70 hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Template buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button variant="tang" size="lg" disabled={!!busy || generating} onClick={() => download('strip')}>
            {busy === 'strip' ? 'Building…' : '↔ Strip'}
          </Button>
          <Button variant="grape" size="lg" disabled={!!busy || generating} onClick={() => download('zine')}>
            {busy === 'zine' ? 'Building…' : '📖 Zine (fold-up)'}
          </Button>
          <Button variant="ghost" size="lg" onClick={onRestart}>
            ↻ Make another
          </Button>
        </div>
        <p className="max-w-md text-center text-xs text-white/50">
          <strong>Strip</strong> reads left-to-right across two rows.{' '}
          <strong>Zine</strong> prints as an 8-page booklet — fold and cut along
          the guides (its top row prints upside-down on purpose).
        </p>
      </div>
    </div>
  )
}

function BlankCell({ color, value, onChange }) {
  return (
    <div
      className="pv-frame flex aspect-[3/2] items-center justify-center p-3"
      style={{ backgroundColor: color }}
    >
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Add a note…"
        rows={2}
        className="w-full resize-none bg-transparent text-center font-display text-lg font-black text-white placeholder:text-white/60 focus:outline-none"
      />
    </div>
  )
}
