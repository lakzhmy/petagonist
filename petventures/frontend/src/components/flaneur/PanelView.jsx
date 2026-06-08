import { getType } from '../../utils/waypointTypes'

/**
 * PanelView — a single comic frame in the result grid. The image already carries
 * its caption + frame from the backend; here we add the soft Petventures frame,
 * paper texture, a number badge, and a little type tag.
 */
export default function PanelView({ panel, index = 0 }) {
  const type = getType(panel.type)
  return (
    <figure className="paper-noise spring relative w-full hover:scale-[1.02]">
      <div className="pv-frame overflow-hidden bg-white">
        <img
          src={panel.image_url}
          alt={panel.location_name}
          className="block w-full"
          loading="lazy"
        />
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
