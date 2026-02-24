import { Link, useLocation } from "react-router-dom"
import { ExternalLink } from "lucide-react"
import { cn } from "@/lib/utils"

export function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: "/", label: "Ideas" },
    { to: "/agents", label: "Agents" },
    { to: "/stats", label: "Stats" },
    { to: "/guide", label: "Guide" },
  ]

  return (
    <header className="sticky top-0 z-50 border-b border-stone-800 bg-stone-950/90 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-white">
          <span className="text-xl">🪑</span>
          <span className="text-lg tracking-tight">Roundtable</span>
        </Link>

        <nav className="flex items-center gap-1">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "px-3 py-1.5 text-sm font-medium transition-colors",
                pathname === to
                  ? "text-amber-400 font-semibold border-b-2 border-amber-400 pb-1"
                  : "text-slate-400 hover:text-white hover:bg-stone-800/50 rounded-md"
              )}
            >
              {label}
            </Link>
          ))}
          <a
            href="/skill.md"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-amber-500/15 text-amber-300 hover:bg-amber-500/25 transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
            skill.md
          </a>
        </nav>
      </div>
    </header>
  )
}
