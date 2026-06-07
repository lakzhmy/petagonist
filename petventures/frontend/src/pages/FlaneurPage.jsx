import { Fragment } from 'react'
import PageWrapper from '../components/layout/PageWrapper'
import Tag from '../components/ui/Tag'

/**
 * FlaneurPage — the Petventures experience and the app's home (root route).
 * The 3-step spine (Your Pet → The Route → The Comic).
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
          <h1 className="mx-auto max-w-2xl font-display text-4xl font-black leading-tight text-white sm:text-5xl">
            Let&apos;s make an awesome pet adventure for your baby!
          </h1>
        </div>

        {/* Stepper — step columns are fixed-width and the connector lines are
            equal flex-1 spacers between them, so the row stays symmetric. */}
        <ol className="mx-auto mt-10 flex max-w-xl items-start justify-between">
          {STEPS.map((s, i) => (
            <Fragment key={s.n}>
              <li className="flex w-20 flex-col items-center gap-2">
                <Tag
                  tone={s.active ? s.tone : 'cream'}
                  className={`h-11 w-11 justify-center !rounded-full text-lg ${s.active ? '' : 'opacity-60'}`}
                >
                  {s.n}
                </Tag>
                <span className={`font-display text-sm font-extrabold ${s.active ? 'text-white' : 'text-white/50'}`}>
                  {s.title}
                </span>
              </li>
              {i < STEPS.length - 1 && (
                <span className="mt-5 h-1 flex-1 rounded-full bg-white/20" />
              )}
            </Fragment>
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
