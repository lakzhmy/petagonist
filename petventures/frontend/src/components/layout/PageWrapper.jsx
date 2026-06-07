import Navbar from './Navbar'
import Footer from './Footer'

/**
 * PageWrapper — shared shell: sticky nav, patterned background surface,
 * footer. `surface` lets each page pick its dominant color block.
 */
const SURFACES = {
  grape: 'bg-grape',
  tang: 'bg-tang',
  cream: 'bg-cream text-ink',
}

export default function PageWrapper({ surface = 'grape', pattern = true, nav = 'minimal', children }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar variant={nav} />
      <main className={`flex-1 ${SURFACES[surface]} ${pattern ? 'paw-pattern' : ''}`}>
        {children}
      </main>
      <Footer />
    </div>
  )
}
