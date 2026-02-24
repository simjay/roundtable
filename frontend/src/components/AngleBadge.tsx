import type { AngleTag } from "@/types"
import { cn } from "@/lib/utils"

const ANGLE_CONFIG: Record<AngleTag, { label: string; className: string }> = {
  market_risk:            { label: "Market Risk",            className: "bg-red-500/15 text-red-400 border-red-500/30" },
  technical_feasibility:  { label: "Technical Feasibility",  className: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
  financial_viability:    { label: "Financial Viability",    className: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
  execution_difficulty:   { label: "Execution Difficulty",   className: "bg-orange-500/15 text-orange-400 border-orange-500/30" },
  ethical_concerns:       { label: "Ethical Concerns",       className: "bg-purple-500/15 text-purple-400 border-purple-500/30" },
  competitive_landscape:  { label: "Competitive Landscape",  className: "bg-teal-500/15 text-teal-400 border-teal-500/30" },
  alternative_approach:   { label: "Alternative Approach",   className: "bg-green-500/15 text-green-400 border-green-500/30" },
  devils_advocate:        { label: "Devil's Advocate",       className: "bg-pink-500/15 text-pink-400 border-pink-500/30" },
}

interface AngleBadgeProps {
  angle: AngleTag
  size?: "sm" | "md"
  dimmed?: boolean
}

export function AngleBadge({ angle, size = "md", dimmed = false }: AngleBadgeProps) {
  const config = ANGLE_CONFIG[angle] ?? { label: angle, className: "bg-slate-500/15 text-slate-400 border-slate-500/30" }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border font-medium",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs",
        config.className,
        dimmed && "opacity-40"
      )}
    >
      {config.label}
    </span>
  )
}

export { ANGLE_CONFIG }
