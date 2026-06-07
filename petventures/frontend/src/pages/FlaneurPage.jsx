import PageWrapper from '../components/layout/PageWrapper'
import Tag from '../components/ui/Tag'
import Sparkle from '../components/ui/Sparkle'

/**
 * FlaneurPage — the 3-step spine (Your Pet → The Route → The Comic).
 * Slice 1 lays out the stepper shell; steps get wired in Slices 2–4.
 */
const STEPS = [
  { n: 1, title: 'Your Pet', tone: 'tang', active: true },
  { n: 2, title: 'The Route', tone: 'grape', active: false },
  { n: 3, title: 'The Comic', tone: 'lime', active: false },
]

export default function FlaneurPage() {
  return (
    <PageWrapper surface="grape">
      <section className="mx-auto max-w-5xl px-5 py-12">
        <div className="text-center">
          <Tag tone="sun" icon={<Sparkle size={14} twinkle />}>
            Pet Flâneur
          </Tag>
          <h1 className="mt-4 font-display text-5xl font-black text-white">
            Let&apos;s make a comic
          </h1>
        </div>

        {/* Stepper */}
        <ol className="mx-auto mt-10 flex max-w-2xl items-center justify-between gap-2">
          {STEPS.map((s, i) => (
            <li key={s.n} className="flex flex-1 items-center gap-2">
              <div className="flex flex-col items-center gap-2">
                <Tag
                  tone={s.active ? s.tone : 'cream'}
                  className={`h-11 w-11 justify-center !rounded-full text-lg ${s.active ? '' : 'opacity-60'}`}
                >
                  {s.n}
                </Tag>
                <span className={`font-display text-sm font-extrabold ${s.active ? 'text-white' : 'text-white/50'}`}>
                  {s.title}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <span className="mb-6 h-1 flex-1 rounded-full bg-white/20" />
              )}
            </li>
          ))}
        </ol>

        {/* Placeholder body */}
        <div className="mt-12 rounded-[var(--radius-card)] border-2 border-dashed border-white/30 bg-white/5 p-14 text-center">
          <span className="animate-bob inline-block text-6xl">🐾</span>
          <p className="mt-4 font-display text-xl font-black text-white">
            Step 1 lands in the next slice
          </p>
          <p className="mt-2 text-white/70">
            The pet uploader and character gallery get wired up next. The shell,
            colors, and motion you see here are the foundation they&apos;ll sit in.
          </p>
        </div>
      </section>
    </PageWrapper>
  )
}
