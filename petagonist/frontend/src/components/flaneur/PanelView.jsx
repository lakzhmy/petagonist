import { getType } from '../../utils/waypointTypes'

/**
 * PanelView — a single comic frame in the result grid. Shows split re-roll
 * buttons on hover: one for the background (scene), one for the character.
 */
export default function PanelView({ panel, index = 0, onRegenerate, rolling = false }) {
  const type = getType(panel.type)
  return (
    <figure className="paper-noise spring group relative w-full hover:scale-[1.02]">
      <div className="pv-frame relative overflow-hidden bg-white">
        <img
          key={panel.image_url}
          src={panel.image_url}
          alt={panel.location_name}
          className="block w-full"
          onError={(e) => {
            const src = e.target.src
            if (!src.includes('&retry=')) {
              e.target.src = src + (src.includes('?') ? '&' : '?') + 'retry=1'
            }
          }}
        />

        {/* Split re-roll buttons — appear on hover */}
        {onRegenerate && !rolling && (
          <div className="spring absolute bottom-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100">
            <button
              type="button"
              onClick={() => onRegenerate('background')}
              title="Re-roll background"
              className="spring grid h-8 w-8 place-items-center rounded-full bg-grape text-sm text-white shadow-[var(--shadow-lift)] hover:bg-tang"
            >
              🏙
            </button>
            <button
              type="button"
              onClick={() => onRegenerate('character')}
              title="Re-roll character"
              className="spring grid h-8 w-8 place-items-center rounded-full bg-grape text-sm text-white shadow-[var(--shadow-lift)] hover:bg-tang"
            >
              🐾
            </button>
            <button
              type="button"
              onClick={() => onRegenerate('all')}
              title="Re-roll both"
              className="spring grid h-8 w-8 place-items-center rounded-full bg-grape text-lg text-white shadow-[var(--shadow-lift)] hover:bg-tang"
            >
              ↻
            </button>
          </div>
        )}

        {/* Dim while a new scene is being drawn */}
        {rolling && (
          <div className="absolute inset-0 grid place-items-center bg-grape/40">
            <span className="font-display text-sm font-black text-white">Re-rolling…</span>
          </div>
        )}
      </div>

      <span className="absolute -right-2 -top-2 grid h-9 w-9 place-items-center rounded-full bg-sun font-display text-sm font-black text-ink shadow-[var(--shadow-lift)]">
        {index + 1}
      </span>
      <figcaption className="mt-2 flex items-center justify-center gap-1.5 text-sm font-bold text-white/80">
        <span>{type.icon}</span>
        <span className="truncate">{panel.location_name}</span>
      </figcaption>
    </figure>
  )
}
