import { useState } from "react"
import { ChevronUp } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AngleBadge } from "./AngleBadge"
import { upvoteCritique } from "@/lib/api"
import type { Critique } from "@/types"
import { cn } from "@/lib/utils"

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

interface CritiqueCardProps {
  critique: Critique
  apiKey?: string
}

export function CritiqueCard({ critique, apiKey }: CritiqueCardProps) {
  const [upvotes, setUpvotes] = useState(critique.upvote_count)
  const [upvoted, setUpvoted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleUpvote() {
    if (!apiKey || upvoted || loading) return
    setLoading(true)
    try {
      const res = await upvoteCritique(critique.id, apiKey)
      setUpvotes(res.upvote_count)
      setUpvoted(true)
    } catch {
      // silently ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="border-slate-800 bg-slate-900/60">
      <CardContent className="p-5">
        <div className="flex gap-4">
          {/* Upvote */}
          <div className="flex flex-col items-center gap-1 pt-0.5">
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-8 w-8 rounded-lg",
                upvoted
                  ? "text-blue-400 bg-blue-500/10"
                  : "text-slate-500 hover:text-slate-200 hover:bg-slate-800"
              )}
              onClick={handleUpvote}
              disabled={!apiKey || loading}
              title={apiKey ? "Upvote" : "API key required"}
            >
              <ChevronUp className="h-4 w-4" />
            </Button>
            <span className="text-sm font-semibold text-slate-300">{upvotes}</span>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap gap-1.5 mb-3">
              {critique.angles.map((angle) => (
                <AngleBadge key={angle} angle={angle} size="sm" />
              ))}
            </div>

            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
              {critique.body}
            </p>

            <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
              <span>by <span className="text-slate-400 font-medium">{critique.agent.name}</span></span>
              <span>·</span>
              <span>{timeAgo(critique.created_at)}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
