import Button from '../ui/Button'
import Tag from '../ui/Tag'
import Sparkle from '../ui/Sparkle'

const MAX = 5

/**
 * PetGallery — grid of generated character variants. Select 1–MAX favourites;
 * a "Continue" CTA appears once at least one is chosen.
 */
export default function PetGallery({ variants, selectedIds, onToggle, onRegenerate, onContinue }) {
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
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {variants.map((v) => {
          const isOn = selected.has(v.id)
          const disabled = !isOn && atMax
          return (
            <button
              key={v.id}
              type="button"
              onClick={() => onToggle(v.id)}
              disabled={disabled}
              aria-pressed={isOn}
              className={[
                'spring group relative overflow-hidden rounded-[var(--radius-card)] text-left',
                'border-4 bg-white/5',
                isOn
                  ? 'border-sun shadow-[var(--shadow-lift)] -translate-y-1'
                  : 'border-transparent hover:-translate-y-1 hover:border-bubble',
                disabled ? 'cursor-not-allowed opacity-40' : 'cursor-pointer',
              ].join(' ')}
            >
              {/* Selection check */}
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
          )
        })}
      </div>

      {/* Actions */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button variant="ghost" size="md" onClick={onRegenerate}>
          ↻ Regenerate
        </Button>
        <Button
          variant="lime"
          size="lg"
          disabled={selected.size === 0}
          onClick={onContinue}
        >
          Continue to the route →
        </Button>
      </div>
    </div>
  )
}
