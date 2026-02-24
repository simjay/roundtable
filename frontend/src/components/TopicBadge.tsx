import type { TopicTag } from "@/types"
import { cn } from "@/lib/utils"

const TOPIC_CONFIG: Record<TopicTag, { label: string; className: string }> = {
  business:  { label: "Business",  className: "bg-blue-500/10 text-blue-300 border-blue-500/20" },
  research:  { label: "Research",  className: "bg-violet-500/10 text-violet-300 border-violet-500/20" },
  product:   { label: "Product",   className: "bg-cyan-500/10 text-cyan-300 border-cyan-500/20" },
  creative:  { label: "Creative",  className: "bg-rose-500/10 text-rose-300 border-rose-500/20" },
  other:     { label: "Other",     className: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
}

export function TopicBadge({ topic }: { topic: TopicTag | null }) {
  if (!topic) return null
  const config = TOPIC_CONFIG[topic]
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </span>
  )
}
