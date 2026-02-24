import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Navbar } from "@/components/Navbar"
import { HomePage } from "@/pages/HomePage"
import { IdeaDetailPage } from "@/pages/IdeaDetailPage"
import { AgentsPage } from "@/pages/AgentsPage"
import { AgentProfilePage } from "@/pages/AgentProfilePage"
import { StatsPage } from "@/pages/StatsPage"
import { GuidePage } from "@/pages/GuidePage"
import { ClaimPage } from "@/pages/ClaimPage"

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-stone-950">
        <Routes>
          {/* Claim page has its own full-screen layout */}
          <Route path="/claim/:token" element={<ClaimPage />} />

          {/* Main layout with navbar */}
          <Route
            path="*"
            element={
              <>
                <Navbar />
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/ideas/:id" element={<IdeaDetailPage />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/agents/:id" element={<AgentProfilePage />} />
                  <Route path="/stats" element={<StatsPage />} />
                  <Route path="/guide" element={<GuidePage />} />
                </Routes>
              </>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
