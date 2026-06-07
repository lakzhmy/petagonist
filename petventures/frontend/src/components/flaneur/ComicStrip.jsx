import { useState } from 'react'
import Button from '../ui/Button'
import Tag from '../ui/Tag'
import Sparkle from '../ui/Sparkle'
import PawIcon from '../ui/PawIcon'
import PanelView from './PanelView'

/**
 * ComicStrip — the finished output. Toggle horizontal strip vs vertical zine,
 * paw-print connectors between panels, and download as PNG or PDF.
 */
export default function ComicStrip({ comic, onRestart }) {
  const [vertical, setVertical] = useState(false)
  const panels = comic?.panels ?? []

  return (
    <div>
      {/* Header / controls */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Tag tone="sun" icon={<Sparkle size={14} twinkle />}>
            Your comic is ready!
          </Tag>
          <h2 className="mt-2 font-display text-3xl font-black text-white">
            A {panels.length}-panel adventure 🎉
          </h2>
        </div>

        <div className="flex items-center gap-1 rounded-full bg-white/10 p-1">
          <button
            onClick={() => setVertical(false)}
            className={`spring rounded-full px-4 py-2 font-display text-sm font-extrabold ${
              !vertical ? 'bg-sun text-ink' : 'text-white/70 hover:text-white'
            }`}
          >
            ↔ Strip
          </button>
          <button
            onClick={() => setVertical(true)}
            className={`spring rounded-full px-4 py-2 font-display text-sm font-extrabold ${
              vertical ? 'bg-sun text-ink' : 'text-white/70 hover:text-white'
            }`}
          >
            ↕ Zine
          </button>
        </div>
      </div>

      {/* Panels */}
      <div
        className={
          vertical
            ? 'flex flex-col items-center gap-3'
            : 'flex items-start gap-3 overflow-x-auto pb-4'
        }
      >
        {panels.map((p, i) => (
          <div
            key={p.order}
            className={vertical ? 'flex flex-col items-center gap-3' : 'flex items-center gap-3'}
          >
            <PanelView panel={p} index={i} vertical={vertical} />
            {i < panels.length - 1 && (
              <PawIcon
                size={26}
                color="var(--color-sun)"
                className={`shrink-0 opacity-80 ${vertical ? 'rotate-90' : ''}`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Downloads + restart */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        {comic?.strip_url && (
          <Button as="a" href={comic.strip_url} download variant="tang" size="lg">
            ⬇ Download PNG
          </Button>
        )}
        {comic?.pdf_url && (
          <Button as="a" href={comic.pdf_url} download variant="grape" size="lg">
            ⬇ Download PDF
          </Button>
        )}
        <Button variant="ghost" size="lg" onClick={onRestart}>
          ↻ Make another
        </Button>
      </div>
    </div>
  )
}
