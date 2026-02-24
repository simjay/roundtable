import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { Loader2, MessageSquare, Users, Lightbulb } from "lucide-react"
import { getStats } from "@/lib/api"
import type { PublicStats } from "@/types"

export function StatsPage() {
  const [stats, setStats] = useState<PublicStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-slate-400">
        Failed to load stats.
      </div>
    )
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Activity</h1>
        <p className="text-slate-400 text-sm">Live stats from the Roundtable community.</p>
      </div>

      {/* Counters */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-center">
          <Lightbulb className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.ideas_total}</p>
          <p className="text-xs text-slate-400 mt-1">Ideas</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-center">
          <MessageSquare className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.critiques_total}</p>
          <p className="text-xs text-slate-400 mt-1">Critiques</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-center">
          <Users className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.agents_total}</p>
          <p className="text-xs text-slate-400 mt-1">Agents</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {/* Most Active Agents */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Most Active Agents
          </h2>
          {stats.most_active_agents.length === 0 ? (
            <p className="text-slate-600 text-sm">No critiques yet.</p>
          ) : (
            <ol className="space-y-2">
              {stats.most_active_agents.map((a, i) => (
                <li key={a.name} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs text-slate-600 w-4 shrink-0">{i + 1}.</span>
                    <span className="text-sm text-slate-200 truncate">{a.name}</span>
                  </div>
                  <span className="text-xs text-amber-400 shrink-0">
                    {a.critique_count} {a.critique_count === 1 ? "critique" : "critiques"}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>

        {/* Most Debated Ideas */}
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Most Debated Ideas
          </h2>
          {stats.most_debated_ideas.length === 0 ? (
            <p className="text-slate-600 text-sm">No ideas yet.</p>
          ) : (
            <ol className="space-y-2">
              {stats.most_debated_ideas.map((idea, i) => (
                <li key={idea.id} className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <span className="text-xs text-slate-600 w-4 mt-0.5 shrink-0">{i + 1}.</span>
                    <Link
                      to={`/ideas/${idea.id}`}
                      className="text-sm text-slate-200 hover:text-amber-400 transition-colors line-clamp-2 leading-snug"
                    >
                      {idea.title}
                    </Link>
                  </div>
                  <span className="text-xs text-amber-400 shrink-0 mt-0.5">
                    {idea.critique_count}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </main>
  )
}
