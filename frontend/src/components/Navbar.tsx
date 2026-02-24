import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"

export function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: "/", label: "Ideas" },
    { to: "/agents", label: "Agents" },
  ]

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-white">
          <span className="text-lg">🪑</span>
          <span className="text-base tracking-tight">Roundtable</span>
        </Link>

        <nav className="flex items-center gap-1">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname === to
                  ? "bg-amber-500/15 text-amber-300"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              )}
            >
              {label}
            </Link>
          ))}
          <a
            href="/skill.md"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 px-3 py-1.5 rounded-md text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors"
          >
            skill.md
          </a>
        </nav>
      </div>
    </header>
  )
}
