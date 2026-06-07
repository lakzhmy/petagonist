import { Link } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Tag from '../components/ui/Tag'
import Sparkle from '../components/ui/Sparkle'
import PawIcon from '../components/ui/PawIcon'

const MODES = [
  {
    to: '/flaneur',
    surface: 'sun',
    emoji: '🗺️',
    title: 'Pet Flâneur',
    tagline: 'Draw a route, get a comic.',
    desc: 'Drop waypoints on a real map and your pet strolls through them in a Tintin-style comic strip.',
    ready: true,
  },
  {
    to: '/ispy',
    surface: 'bubble',
    emoji: '🔍',
    title: 'I-SPY: Hergé City',
    tagline: 'Find your pet in a crowd.',
    desc: 'Your pet hides in a bustling ligne-claire cityscape. Can your friends spot them?',
    ready: false,
  },
  {
    to: '/isobuild',
    surface: 'lime',
    emoji: '🏗️',
    title: 'IsoBuild',
    tagline: 'Build a city, hide your pet.',
    desc: 'Stack an isometric toy city block by block, then render it as an illustrated postcard.',
    ready: false,
  },
]

export default function LandingPage() {
  return (
    <PageWrapper surface="grape" nav="modes">
      {/* ---------- Hero ---------- */}
      <section className="relative mx-auto max-w-7xl px-5 pb-10 pt-16 text-center">
        <div className="mx-auto max-w-3xl">
          <span className="mb-5 inline-flex">
            <Tag tone="sun" icon={<Sparkle size={14} twinkle />}>
              A playful pet-comic generator
            </Tag>
          </span>

          <h1 className="relative font-display text-6xl font-black leading-[0.95] text-white sm:text-7xl md:text-8xl">
            Send your pet on an
            <span className="relative mx-2 inline-block tilt-right text-sun">
              adventure
              <Sparkle
                size={32}
                color="var(--color-bubble)"
                twinkle
                className="absolute -right-8 -top-4"
              />
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg text-white/80">
            Upload a photo, draw a route through a real city, and get back an
            illustrated comic strip of your pet exploring the streets — in bold{' '}
            <em>ligne claire</em> style.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Button as={Link} to="/flaneur" variant="tang" size="lg">
              <PawIcon size={20} color="white" /> Start with Pet Flâneur
            </Button>
            <Button as="a" href="#modes" variant="ghost" size="lg">
              See the three modes
            </Button>
          </div>
        </div>

        {/* floating decorative sparkles */}
        <Sparkle size={26} color="var(--color-sun)" className="absolute left-8 top-24 animate-bob hidden md:block" />
        <Sparkle size={20} color="var(--color-lime)" className="absolute right-14 top-40 animate-twinkle hidden md:block" />
        <Sparkle size={18} color="var(--color-bubble)" className="absolute left-24 bottom-6 animate-twinkle hidden md:block" />
      </section>

      {/* ---------- Three modes ---------- */}
      <section id="modes" className="mx-auto max-w-7xl scroll-mt-20 px-5 pb-20">
        <h2 className="mb-2 text-center font-display text-3xl font-black text-white">
          Three ways to play
        </h2>
        <p className="mb-8 text-center text-white/70">
          One pet, three little universes. Start with Flâneur — the rest are on the way.
        </p>

        <div className="grid gap-5 md:grid-cols-3">
          {MODES.map((m) => (
            <Card
              key={m.to}
              as={m.ready ? Link : 'div'}
              to={m.ready ? m.to : undefined}
              surface={m.surface}
              interactive={m.ready}
              className={`relative flex flex-col ${!m.ready ? 'opacity-95' : ''}`}
            >
              <div className="mb-4 flex items-start justify-between">
                <span className="grid h-16 w-16 place-items-center rounded-2xl bg-white/35 text-4xl">
                  {m.emoji}
                </span>
                {m.ready ? (
                  <Tag tone="ink" icon={<Sparkle size={12} />}>
                    Ready
                  </Tag>
                ) : (
                  <Tag tone="ink">Coming soon</Tag>
                )}
              </div>

              <h3 className="font-display text-2xl font-black">{m.title}</h3>
              <p className="mt-1 font-display font-bold opacity-80">{m.tagline}</p>
              <p className="mt-3 text-sm opacity-90">{m.desc}</p>

              <div className="mt-5 flex items-center gap-1 font-display font-extrabold">
                {m.ready ? (
                  <>
                    Let&apos;s go <span className="transition-transform group-hover:translate-x-1">→</span>
                  </>
                ) : (
                  <span className="opacity-70">In the workshop…</span>
                )}
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* ---------- How it works strip ---------- */}
      <section className="bg-cream py-16 text-ink">
        <div className="mx-auto max-w-5xl px-5">
          <h2 className="mb-10 text-center font-display text-3xl font-black">
            How Pet Flâneur works
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              { n: '1', tone: 'tang', title: 'Your Pet', body: 'Upload a photo and pick your favourite comic-character variants.' },
              { n: '2', tone: 'grape', title: 'The Route', body: 'Drop waypoints on a real city map to plot the stroll.' },
              { n: '3', tone: 'lime', title: 'The Comic', body: 'Generate a multi-panel strip and download it to share.' },
            ].map((s) => (
              <div key={s.n} className="flex flex-col items-center text-center">
                <Tag tone={s.tone} className="mb-3 h-10 w-10 justify-center !rounded-full text-lg">
                  {s.n}
                </Tag>
                <h3 className="font-display text-xl font-black">{s.title}</h3>
                <p className="mt-2 text-sm text-ink/70">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </PageWrapper>
  )
}
