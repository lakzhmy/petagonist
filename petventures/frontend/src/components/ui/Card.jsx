/**
 * Card — a confident color-blocked surface with generous radius and a
 * springy lift on hover when interactive. The workhorse container.
 */
const SURFACES = {
  cream: 'bg-cream text-ink',
  white: 'bg-white text-ink',
  grape: 'bg-grape text-white',
  tang: 'bg-tang text-white',
  sun: 'bg-sun text-ink',
  bubble: 'bg-bubble text-white',
  lime: 'bg-lime text-ink',
  sky: 'bg-sky text-ink',
}

export default function Card({
  as: Comp = 'div',
  surface = 'cream',
  interactive = false,
  className = '',
  children,
  ...props
}) {
  return (
    <Comp
      className={[
        'rounded-[var(--radius-card)] p-6',
        SURFACES[surface],
        interactive
          ? 'spring cursor-pointer hover:-translate-y-1.5 hover:rotate-[-0.6deg] hover:shadow-[var(--shadow-lift)]'
          : '',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </Comp>
  )
}
