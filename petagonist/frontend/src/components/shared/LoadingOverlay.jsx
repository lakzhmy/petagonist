import { useEffect, useState } from 'react'
import PawIcon from '../ui/PawIcon'
import Sparkle from '../ui/Sparkle'

const MESSAGES = [
  'Teaching your pet to read maps…',
  'Convincing pigeons to pose…',
  'Drawing tiny cobblestones…',
  'Pressing the perfect little beret…',
  'Sharpening the ligne claire…',
  'Scattering crumbs for the birds…',
  'Warming up the comic printer…',
]

/** Full-screen playful loading state with rotating messages. */
export default function LoadingOverlay({ show, messages = MESSAGES }) {
  const [i, setI] = useState(0)

  useEffect(() => {
    if (!show) return
    setI(0)
    const t = setInterval(() => setI((n) => (n + 1) % messages.length), 1800)
    return () => clearInterval(t)
  }, [show, messages.length])

  if (!show) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-grape/90 backdrop-blur-sm paw-pattern">
      <div className="flex flex-col items-center text-center">
        <div className="relative">
          <span className="grid h-24 w-24 place-items-center rounded-full bg-sun shadow-[var(--shadow-lift)] animate-bob">
            <PawIcon size={52} color="var(--color-grape)" />
          </span>
          <Sparkle size={26} color="var(--color-bubble)" twinkle className="absolute -right-3 -top-2" />
          <Sparkle size={18} color="var(--color-lime)" twinkle className="absolute -left-4 bottom-0" />
        </div>
        <p className="mt-7 font-display text-2xl font-black text-white" key={i}>
          {messages[i]}
        </p>
        <p className="mt-2 text-white/60">Hang tight — real magic in progress</p>
      </div>
    </div>
  )
}
