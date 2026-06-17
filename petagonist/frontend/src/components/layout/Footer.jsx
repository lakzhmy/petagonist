import PawIcon from '../ui/PawIcon'

export default function Footer() {
  return (
    <footer className="mt-auto bg-grape-deep px-5 py-8 text-white/70">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-2 text-center text-sm">
        <div className="flex items-center gap-1.5 font-display font-bold text-white">
          <PawIcon size={18} color="var(--color-sun)" />
          <span>Pet<span className="text-sun">agonist</span></span>
        </div>
        <p>
          A MaCAD - GenAI Project · Turn your pet into a comic-book adventurer.
        </p>
        <p className="text-xs text-white/40">Powered by snoot boops and pixel dust.</p>
      </div>
    </footer>
  )
}
