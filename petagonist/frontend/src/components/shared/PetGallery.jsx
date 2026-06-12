import { useState } from 'react'
import Button from '../ui/Button'
import Tag from '../ui/Tag'
import Sparkle from '../ui/Sparkle'

const MAX = 5

export default function PetGallery({
  variants,
  selectedIds,
  onToggle,
  onRegenerate,
  onRegenerateOne,
  onGenerateMore,
  onContinue,
  onBack,
  generating,
  progress,
}) {
  const selected = new Set(selectedIds)
  const atMax = selected.size >= MAX

  return (
    <div>
      <div className="mb-6 text-center">
        <Tag tone="sun" icon={<Sparkle size={14} twinkle />}>
          Pick your favourites
        </Tag>
        <p className="mt-3 text-white/80">
          Choose <strong>1–{MAX}</strong> characters to star in your comic.
          <span className="ml-2 font-display font-extrabold text-sun">
            {selected.size}/{MAX} selected
          </span>
        </p>
        {generating && progress && (
          <p className="mt-2 font-display text-sm font-bold text-bubble animate-pulse">
            Generating {progress.done} of {progress.total}…
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {variants.map((v) => {
          const isOn = selected.has(v.id)
          const disabled = !isOn && atMax
          return (
            <VariantCard
              key={v.id}
              variant={v}
              isOn={isOn}
              disabled={disabled}
              onToggle={() => onToggle(v.id)}
              onRegenerate={onRegenerateOne ? () => onRegenerateOne(v.id) : null}
            />
          )
        })}

        {generating && progress && progress.done < progress.total && (
          <div className="grid aspect-square place-items-center rounded-[var(--radius-card)] border-4 border-dashed border-white/20 bg-white/5">
            <div className="text-center">
              <span className="inline-block animate-bob text-4xl">🎨</span>
              <p className="mt-2 px-3 font-display text-xs font-bold text-white/60">
                Drawing…
              </p>
            </div>
          </div>
        )}

        {!generating && onGenerateMore && (
          <button
            type="button"
            onClick={onGenerateMore}
            className="spring grid aspect-square place-items-center rounded-[var(--radius-card)] border-4 border-dashed border-white/20 bg-white/5 hover:border-bubble hover:bg-white/10 cursor-pointer"
          >
            <div className="text-center">
              <span className="text-3xl text-white/50">+</span>
              <p className="mt-1 px-3 font-display text-xs font-bold text-white/50">
                More
              </p>
            </div>
          </button>
        )}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        {onBack && (
          <Button variant="ghost" size="md" onClick={onBack}>
            ← Different pet
          </Button>
        )}
        <Button variant="ghost" size="md" onClick={onRegenerate} disabled={generating}>
          ↻ Regenerate all
        </Button>
        <Button
          variant="lime"
          size="lg"
          disabled={selected.size === 0 || generating}
          onClick={onContinue}
        >
          Continue to the route →
        </Button>
      </div>
    </div>
  )
}

function VariantCard({ variant: v, isOn, disabled, onToggle, onRegenerate }) {
  const [regenerating, setRegenerating] = useState(false)

  async function handleRegenOne(e) {
    e.stopPropagation()
    if (!onRegenerate || regenerating) return
    setRegenerating(true)
    try {
      await onRegenerate()
    } finally {
      setRegenerating(false)
    }
  }

  return (
    <div className="group relative">
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled || regenerating}
        aria-pressed={isOn}
        className={[
          'spring w-full overflow-hidden rounded-[var(--radius-card)] text-left',
          'border-4 bg-white/5',
          isOn
            ? 'border-sun shadow-[var(--shadow-lift)] -translate-y-1'
            : 'border-transparent hover:-translate-y-1 hover:border-bubble',
          disabled ? 'cursor-not-allowed opacity-40' : 'cursor-pointer',
          regenerating ? 'opacity-50' : '',
        ].join(' ')}
      >
        <span
          className={[
            'spring absolute right-2 top-2 z-10 grid h-8 w-8 place-items-center rounded-full font-black',
            isOn ? 'bg-sun text-ink scale-100' : 'bg-black/30 text-white/70 scale-90',
          ].join(' ')}
        >
          {isOn ? '✓' : '+'}
        </span>

        <img
          src={v.image_url}
          alt={v.pose_prompt}
          loading="lazy"
          className="aspect-square w-full object-cover"
        />
      </button>

      {onRegenerate && (
        <button
          type="button"
          onClick={handleRegenOne}
          disabled={regenerating}
          title="Regenerate this variant"
          className={[
            'spring absolute bottom-3 right-3 z-10 grid h-7 w-7 place-items-center',
            'rounded-full bg-black/60 text-white/80 text-xs',
            'opacity-0 group-hover:opacity-100',
            'hover:bg-grape hover:text-white hover:scale-110',
            regenerating ? '!opacity-100 animate-spin' : '',
          ].join(' ')}
        >
          ↻
        </button>
      )}
    </div>
  )
}
