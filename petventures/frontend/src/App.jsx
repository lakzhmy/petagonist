import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import FlaneurPage from './pages/FlaneurPage'
import ComingSoonPage from './pages/ComingSoonPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/flaneur" element={<FlaneurPage />} />
      <Route
        path="/ispy"
        element={
          <ComingSoonPage
            emoji="🔍"
            title="I-SPY: Hergé City"
            teaser="Soon you'll hide your pet in a teeming Tintin-style cityscape and challenge your friends to find them. The crowd is still being drawn."
          />
        }
      />
      <Route
        path="/isobuild"
        element={
          <ComingSoonPage
            emoji="🏗️"
            title="IsoBuild: Pet City"
            teaser="Soon you'll stack an isometric toy city block by block, then render it into an illustrated postcard with your pet living in it. The bricks are still drying."
          />
        }
      />
      <Route
        path="*"
        element={
          <ComingSoonPage
            emoji="🐾"
            title="Lost the trail"
            teaser="This page wandered off. Let's get you back to the adventure."
          />
        }
      />
    </Routes>
  )
}
