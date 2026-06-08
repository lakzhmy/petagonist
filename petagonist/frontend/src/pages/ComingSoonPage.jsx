import { Link } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import Button from '../components/ui/Button'
import Tag from '../components/ui/Tag'
import Sparkle from '../components/ui/Sparkle'

/** Friendly placeholder for modes still in the workshop (I-SPY, IsoBuild). */
export default function ComingSoonPage({ emoji = '🛠️', title, teaser, surface = 'grape' }) {
  return (
    <PageWrapper surface={surface}>
      <section className="mx-auto flex max-w-2xl flex-col items-center px-5 py-28 text-center">
        <span className="animate-bob text-7xl">{emoji}</span>
        <Tag tone="sun" className="mt-6" icon={<Sparkle size={14} twinkle />}>
          Coming soon
        </Tag>
        <h1 className="mt-4 font-display text-5xl font-black text-white">{title}</h1>
        <p className="mt-4 max-w-md text-lg text-white/80">{teaser}</p>
        <div className="mt-8 flex gap-3">
          <Button as={Link} to="/flaneur" variant="tang" size="lg">
            Try Pet Flâneur instead
          </Button>
          <Button as={Link} to="/" variant="ghost" size="lg">
            Back home
          </Button>
        </div>
      </section>
    </PageWrapper>
  )
}
