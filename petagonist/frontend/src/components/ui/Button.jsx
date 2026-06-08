/**
 * Button — full-round, bold, with a springy bounce-on-hover.
 * Variants map to the palette; all share the signature motion.
 */
const VARIANTS = {
  tang: 'bg-tang text-white shadow-[var(--shadow-tang)] hover:shadow-[var(--shadow-lift)]',
  grape: 'bg-grape text-white shadow-[var(--shadow-grape)] hover:shadow-[var(--shadow-lift)]',
  sun: 'bg-sun text-ink shadow-[0_14px_30px_-10px_rgba(255,215,0,0.5)] hover:shadow-[var(--shadow-lift)]',
  lime: 'bg-lime text-ink shadow-[0_14px_30px_-10px_rgba(126,217,87,0.5)] hover:shadow-[var(--shadow-lift)]',
  ghost: 'bg-transparent text-white border-2 border-white/70 hover:border-white hover:bg-white/10',
  outline: 'bg-white text-ink border-2 border-ink hover:bg-cream',
}

const SIZES = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
}

export default function Button({
  as: Comp = 'button',
  variant = 'tang',
  size = 'md',
  className = '',
  children,
  disabled = false,
  ...props
}) {
  return (
    <Comp
      disabled={Comp === 'button' ? disabled : undefined}
      aria-disabled={disabled || undefined}
      className={[
        'spring inline-flex items-center justify-center gap-2 rounded-full font-display font-extrabold',
        'cursor-pointer select-none active:scale-95',
        'hover:-translate-y-0.5 hover:scale-[1.03]',
        'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white/60',
        disabled ? 'pointer-events-none opacity-50 saturate-50' : '',
        VARIANTS[variant],
        SIZES[size],
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </Comp>
  )
}
