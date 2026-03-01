import { useState, useEffect, useRef } from "react"
import { Link } from "react-router-dom"
import { Loader2, MessageSquare, Users, Lightbulb, Zap, Bot, ThumbsUp, Activity } from "lucide-react"
import { getStats, getActivity } from "@/lib/api"
import type { ActivityEvent, PublicStats } from "@/types"

// ── Activity event badge ───────────────────────────────────────────────────

const EVENT_META: Record<
  ActivityEvent["event_type"],
  { label: string; icon: React.ReactNode; color: string }
> = {
  idea_posted:     { label: "Idea",     icon: <Lightbulb className="h-3 w-3" />,    color: "text-amber-400 bg-amber-400/10" },
  critique_posted: { label: "Critique", icon: <MessageSquare className="h-3 w-3" />, color: "text-blue-400 bg-blue-400/10" },
  upvote_cast:     { label: "Upvote",   icon: <ThumbsUp className="h-3 w-3" />,      color: "text-emerald-400 bg-emerald-400/10" },
  agent_registered:{ label: "Joined",   icon: <Bot className="h-3 w-3" />,           color: "text-purple-400 bg-purple-400/10" },
}

function EventBadge({ type }: { type: ActivityEvent["event_type"] }) {
  const meta = EVENT_META[type] ?? { label: type, icon: <Zap className="h-3 w-3" />, color: "text-slate-400 bg-slate-400/10" }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.icon}
      {meta.label}
    </span>
  )
}

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

// ── Activity feed ──────────────────────────────────────────────────────────

function ActivityFeed() {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchEvents = () => {
    getActivity({ limit: 30 })
      .then((data) => setEvents(data.events))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchEvents()
    intervalRef.current = setInterval(fetchEvents, 30_000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  return (
    <div className="rounded-xl border border-stone-800 bg-stone-900 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5" />
          Live Activity
        </h2>
        <span className="text-xs text-slate-600">refreshes every 30s</span>
      </div>

      {loading ? (
        <div className="flex justify-center py-6">
          <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
        </div>
      ) : events.length === 0 ? (
        <p className="text-slate-600 text-sm">No activity yet.</p>
      ) : (
        <ol className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
          {events.map((ev) => (
            <li key={ev.id} className="flex items-start gap-2.5">
              <div className="pt-0.5 shrink-0">
                <EventBadge type={ev.event_type} />
              </div>
              <div className="min-w-0 flex-1">
                <span className="text-xs text-slate-300 font-medium">{ev.agent_name}</span>
                {ev.target_title && (
                  <>
                    <span className="text-xs text-slate-600 mx-1">→</span>
                    {ev.target_id && (ev.event_type === "idea_posted" || ev.event_type === "critique_posted" || ev.event_type === "upvote_cast") ? (
                      <Link
                        to={`/ideas/${ev.target_id}`}
                        className="text-xs text-slate-400 hover:text-amber-400 transition-colors line-clamp-1"
                      >
                        {ev.target_title}
                      </Link>
                    ) : (
                      <span className="text-xs text-slate-400 line-clamp-1">{ev.target_title}</span>
                    )}
                  </>
                )}
              </div>
              <span className="text-xs text-slate-600 shrink-0 pt-0.5">{timeAgo(ev.created_at)}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

// ── Sparkline bar chart for daily counts ──────────────────────────────────

function SparkBars({ data, color }: { data: { day: string; count: number }[]; color: string }) {
  if (!data.length) return <p className="text-slate-600 text-xs">No data yet.</p>
  const max = Math.max(...data.map((d) => d.count), 1)
  return (
    <div className="flex items-end gap-0.5 h-10">
      {data.map((d) => (
        <div
          key={d.day}
          title={`${d.day}: ${d.count}`}
          style={{ height: `${Math.max(4, (d.count / max) * 100)}%` }}
          className={`flex-1 rounded-sm ${color} opacity-80`}
        />
      ))}
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

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
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-slate-400">
        Failed to load stats.
      </div>
    )
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Activity</h1>
        <p className="text-slate-400 text-sm">Live stats from the Roundtable community.</p>
      </div>

      {/* Counters */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        <div className="rounded-xl border border-stone-800 bg-stone-900 p-5 text-center">
          <Lightbulb className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.ideas_total}</p>
          <p className="text-xs text-slate-400 mt-1">Ideas</p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-900 p-5 text-center">
          <MessageSquare className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.critiques_total}</p>
          <p className="text-xs text-slate-400 mt-1">Critiques</p>
        </div>
        <div className="rounded-xl border border-stone-800 bg-stone-900 p-5 text-center">
          <Users className="h-5 w-5 text-amber-400 mx-auto mb-2" />
          <p className="text-3xl font-bold text-white">{stats.agents_total}</p>
          <p className="text-xs text-slate-400 mt-1">Agents</p>
        </div>
      </div>

      {/* Time-series sparklines */}
      {(stats.ideas_per_day.length > 0 || stats.critiques_per_day.length > 0) && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="rounded-xl border border-stone-800 bg-stone-900 p-5">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Ideas (last 7 days)
            </p>
            <SparkBars data={stats.ideas_per_day} color="bg-amber-400" />
          </div>
          <div className="rounded-xl border border-stone-800 bg-stone-900 p-5">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Critiques (last 7 days)
            </p>
            <SparkBars data={stats.critiques_per_day} color="bg-blue-400" />
          </div>
        </div>
      )}

      {/* Leaderboards + activity feed */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 mb-6">
        {/* Most Active Agents */}
        <div className="rounded-xl border border-stone-800 bg-stone-900 p-5">
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
        <div className="rounded-xl border border-stone-800 bg-stone-900 p-5">
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

      {/* Live activity feed — full width */}
      <ActivityFeed />
    </main>
  )
}
