import { getType } from '../../utils/waypointTypes'

/**
 * PanelView — a single comic frame in the result grid. The image already carries
 * its caption + frame from the backend; here we add the soft Petagonist frame,
 * paper texture, a number badge, a type tag, and a ↻ re-roll button that swaps
 * this stop for a different scene + pose.
 */
export default function PanelView({ panel, index = 0, onRegenerate, rolling = false }) {
  const type = getType(panel.type)
  return (
    <figure className="paper-noise spring group relative w-full hover:scale-[1.02]">
      <div className="pv-frame relative overflow-hidden bg-white">
        <img
          src={panel.image_url}
          alt={panel.location_name}
          className="block w-full"
          loading="lazy"
        />

        {/* Re-roll button — appears on hover; spins while rolling */}
        {onRegenerate && (
          <button
            type="button"
            onClick={onRegenerate}
            disabled={rolling}
            aria-label={`Regenerate ${panel.location_name}`}
            title="Re-roll this panel"
            className={`spring absolute bottom-2 right-2 grid h-9 w-9 place-items-center rounded-full bg-grape text-lg text-white shadow-[var(--shadow-lift)] hover:bg-tang ${
              rolling ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
          >
            <span className={rolling ? 'inline-block animate-spin' : ''}>↻</span>
          </button>
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
