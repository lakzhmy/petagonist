import { Link, NavLink } from 'react-router-dom'
import PawIcon from '../ui/PawIcon'
import Tag from '../ui/Tag'

// Mode switcher — only used by the parked multi-mode landing (variant="modes").
// The live Petagonist demo uses the minimal navbar (logo only).
const MODES = [
  { to: '/flaneur', label: 'Pet Flâneur', ready: true },
  { to: '/ispy', label: 'I-SPY', ready: false },
  { to: '/isobuild', label: 'IsoBuild', ready: false },
]

function Logo({ className = '' }) {
  return (
    <Link to="/" className={`spring flex items-center gap-2 hover:scale-[1.03] ${className}`}>
      <span className="grid h-10 w-10 place-items-center rounded-full bg-sun text-ink shadow-[var(--shadow-grape)]">
        <PawIcon size={22} color="var(--color-grape)" />
      </span>
      <span className="font-display text-2xl font-black tracking-tight text-white">
        Pet<span className="text-sun">agonist</span>
      </span>
    </Link>
  )
}

/**
 * Navbar
 *  - variant="minimal" (default): just the centered logo. Used by the
 *    single-experience Petagonist demo.
 *  - variant="modes": logo + mode switcher. Kept for the parked landing page.
 */
export default function Navbar({ variant = 'minimal' }) {
  if (variant === 'minimal') {
    return (
      <header className="sticky top-0 z-40 bg-grape/85 backdrop-blur-md">
        <nav className="mx-auto flex max-w-7xl items-center justify-center px-5 py-3">
          <Logo />
        </nav>
      </header>
    )
  }

  return (
    <header className="sticky top-0 z-40 bg-grape/85 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
        <Logo />
        <div className="flex items-center gap-1 rounded-full bg-white/10 p-1">
          {MODES.map((m) => (
            <NavLink
              key={m.to}
              to={m.to}
              className={({ isActive }) =>
                [
                  'spring relative rounded-full px-4 py-2 font-display text-sm font-extrabold',
                  isActive ? 'bg-sun text-ink' : 'text-white/80 hover:text-white hover:bg-white/10',
                ].join(' ')
              }
            >
              <span className="flex items-center gap-1.5">
                {m.label}
                {!m.ready && (
                  <Tag tone="tang" className="px-1.5 py-0.5 text-[10px]">
                    soon
                  </Tag>
                )}
              </span>
            </NavLink>
          ))}
        </div>
      </nav>
    </header>
  )
}
