/**
 * Tag — the little rounded pill used everywhere: pose labels, coordinates,
 * "Coming Soon", status chips. Bold fill, contrasting text.
 */
const TONES = {
  sun: 'bg-sun text-ink',
  tang: 'bg-tang text-white',
  bubble: 'bg-bubble text-white',
  lime: 'bg-lime text-ink',
  grape: 'bg-grape text-white',
  sky: 'bg-sky text-ink',
  ink: 'bg-ink text-white',
  cream: 'bg-cream text-ink',
}

export default function Tag({ tone = 'sun', className = '', children, icon = null }) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1',
        'font-display text-sm font-extrabold leading-none',
        TONES[tone],
        className,
      ].join(' ')}
    >
      {icon}
      {children}
    </span>
  )
}
