import { getType } from '../../utils/waypointTypes'

/**
 * PanelView — a single comic frame. The image already carries its caption +
 * frame from the backend; here we add the playful tilt, paper texture, and a
 * little type tag so each panel has personality.
 */
const TILTS = ['tilt-left', 'tilt-right', '', 'tilt-right', 'tilt-left']

export default function PanelView({ panel, index = 0, vertical = false }) {
  const type = getType(panel.type)
  return (
    <figure
      className={`paper-noise spring relative shrink-0 ${TILTS[index % TILTS.length]} ${
        vertical ? 'w-full max-w-2xl' : 'w-[320px]'
      } hover:rotate-0 hover:scale-[1.02]`}
    >
      <div className="comic-frame overflow-hidden bg-white">
        <img src={panel.image_url} alt={panel.location_name} className="block w-full" loading="lazy" />
      </div>
      <span className="absolute -right-2 -top-2 grid h-9 w-9 place-items-center rounded-full border-2 border-ink bg-sun font-display text-sm font-black text-ink shadow-[2px_2px_0_0_var(--color-ink)]">
        {index + 1}
      </span>
      <figcaption className="mt-2 flex items-center justify-center gap-1.5 text-sm font-bold text-white/80">
        <span>{type.icon}</span>
        <span className="truncate">{panel.location_name}</span>
      </figcaption>
    </figure>
  )
}
