import { useRef, useState } from 'react'
import Button from '../ui/Button'
import Sparkle from '../ui/Sparkle'
import PawIcon from '../ui/PawIcon'

const ACCEPT = 'image/jpeg,image/png,image/webp'

/**
 * PetUploader — drag-and-drop pet photo + description, then "Generate".
 * Calls onSubmit({ file, description }); parent handles the API + transition.
 */
export default function PetUploader({ onSubmit, loading = false }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [description, setDescription] = useState('')
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  function accept(f) {
    if (!f) return
    if (!ACCEPT.split(',').includes(f.type)) {
      setError('Please pick a JPG, PNG, or WebP image.')
      return
    }
    setError('')
    setFile(f)
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return URL.createObjectURL(f)
    })
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    accept(e.dataTransfer.files?.[0])
  }

  return (
    <div className="mx-auto max-w-xl">
      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={[
          'spring relative grid cursor-pointer place-items-center rounded-[var(--radius-card)]',
          'border-4 border-dashed p-8 text-center',
          dragging
            ? 'border-tang bg-tang/10 scale-[1.01]'
            : 'border-white/40 bg-white/5 hover:border-bubble hover:bg-white/10',
        ].join(' ')}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => accept(e.target.files?.[0])}
        />

        {preview ? (
          <div className="flex flex-col items-center">
            <div className="relative">
              <img
                src={preview}
                alt="Your pet"
                className="h-40 w-40 rounded-full border-4 border-sun object-cover shadow-[var(--shadow-lift)]"
              />
              <Sparkle size={24} color="var(--color-bubble)" twinkle className="absolute -right-2 -top-1" />
            </div>
            <p className="mt-4 font-display font-extrabold text-white">Looking good! 🐾</p>
            <p className="text-sm text-white/60">Click to choose a different photo</p>
          </div>
        ) : (
          <div className="flex flex-col items-center py-4">
            <span className="grid h-20 w-20 place-items-center rounded-full bg-white/15 animate-bob">
              <PawIcon size={40} color="var(--color-sun)" />
            </span>
            <p className="mt-4 font-display text-xl font-black text-white">
              Drop your pet&apos;s photo here
            </p>
            <p className="mt-1 text-sm text-white/60">
              or click to browse · JPG, PNG, WebP · <span className="italic">optional</span>
            </p>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-3 text-center font-display font-bold text-sun">{error}</p>
      )}

      {/* Description */}
      <label className="mt-6 block">
        <span className="font-display font-extrabold text-white">Describe your pet</span>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. a fluffy ginger cat with one white sock"
          className="mt-2 w-full rounded-full border-2 border-white/20 bg-white/10 px-5 py-3 text-white placeholder:text-white/40 focus:border-sun focus:outline-none"
        />
      </label>

      {/* CTA — a photo OR a description is enough (both is best). */}
      <div className="mt-7 flex flex-col items-center gap-2">
        <Button
          variant="tang"
          size="lg"
          disabled={(!file && !description.trim()) || loading}
          onClick={() => onSubmit?.({ file, description })}
        >
          <Sparkle size={18} color="white" />
          {loading ? 'Conjuring characters…' : 'Generate Character'}
        </Button>
        <p className="text-sm text-white/60">
          Add a photo, a description, or both — whatever you&apos;ve got. 🐾
        </p>
      </div>
    </div>
  )
}
