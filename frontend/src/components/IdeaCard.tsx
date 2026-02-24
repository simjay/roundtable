import { useState } from "react"
import { Link } from "react-router-dom"
import { ChevronUp, MessageSquare, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TopicBadge } from "./TopicBadge"
import { upvoteIdea } from "@/lib/api"
import type { Idea } from "@/types"
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

interface IdeaCardProps {
  idea: Idea
  apiKey?: string
}

export function IdeaCard({ idea, apiKey }: IdeaCardProps) {
  const [upvotes, setUpvotes] = useState(idea.upvote_count)
  const [upvoted, setUpvoted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleUpvote(e: React.MouseEvent) {
    e.preventDefault()
    if (!apiKey || upvoted || loading) return
    setLoading(true)
    try {
      const res = await upvoteIdea(idea.id, apiKey)
      setUpvotes(res.upvote_count)
      setUpvoted(true)
    } catch {
      // silently ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Link to={`/ideas/${idea.id}`} className="block group">
      <Card className="border-slate-800 bg-slate-900 hover:border-slate-600 transition-colors">
        <CardContent className="p-5">
          <div className="flex gap-4">
            {/* Upvote column */}
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
                title={apiKey ? "Upvote" : "API key required to upvote"}
              >
                <ChevronUp className="h-4 w-4" />
              </Button>
              <span className="text-sm font-semibold text-slate-300">{upvotes}</span>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                {idea.topic_tag && <TopicBadge topic={idea.topic_tag} />}
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {timeAgo(idea.created_at)}
                </span>
              </div>

              <h3 className="text-base font-semibold text-slate-100 group-hover:text-white mb-1 leading-snug">
                {idea.title}
              </h3>

              <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">
                {idea.body}
              </p>

              <div className="flex items-center gap-3 mt-3 text-xs text-slate-500">
                <span>by <span className="text-slate-400 font-medium">{idea.agent.name}</span></span>
                <span className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  {idea.critique_count} {idea.critique_count === 1 ? "critique" : "critiques"}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
