import PawIcon from '../ui/PawIcon'

export default function Footer() {
  return (
    <footer className="mt-auto bg-grape-deep px-5 py-8 text-white/70">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-2 text-center text-sm">
        <div className="flex items-center gap-2 font-display font-bold text-white">
          <PawIcon size={18} color="var(--color-sun)" />
          Petventures
        </div>
        <p>
          A MACAD thesis project · Turn your pet into a Tintin-style adventurer.
        </p>
        <p className="text-xs text-white/40">Made with bold colors and too much fun.</p>
      </div>
    </footer>
  )
}
