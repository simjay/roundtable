import type { AngleTag } from "@/types"
import { AngleBadge, ANGLE_CONFIG } from "./AngleBadge"

const ALL_ANGLES = Object.keys(ANGLE_CONFIG) as AngleTag[]

interface AngleCoverageBarProps {
  covered: AngleTag[]
}

export function AngleCoverageBar({ covered }: AngleCoverageBarProps) {
  const coveredSet = new Set(covered)
  const uncovered = ALL_ANGLES.filter((a) => !coveredSet.has(a))

  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900/50 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Angle Coverage
        </p>
        <span className="text-xs text-slate-500">
          {covered.length} / {ALL_ANGLES.length} covered
        </span>
      </div>

      {covered.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-2">Covered</p>
          <div className="flex flex-wrap gap-1.5">
            {covered.map((angle) => (
              <AngleBadge key={angle} angle={angle} size="sm" />
            ))}
          </div>
        </div>
      )}

      {uncovered.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-2">Not yet covered - add your perspective</p>
          <div className="flex flex-wrap gap-1.5">
            {uncovered.map((angle) => (
              <AngleBadge key={angle} angle={angle} size="sm" dimmed />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
