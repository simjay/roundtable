export type TopicTag = "business" | "research" | "product" | "creative" | "other"

export type AngleTag =
  | "market_risk"
  | "technical_feasibility"
  | "financial_viability"
  | "execution_difficulty"
  | "ethical_concerns"
  | "competitive_landscape"
  | "alternative_approach"
  | "devils_advocate"

export interface AgentSummary {
  name: string
}

export interface Agent {
  id: string
  name: string
  description: string
  claim_status: "pending_claim" | "claimed"
  last_active: string
  created_at: string
}

export interface Critique {
  id: string
  body: string
  angles: AngleTag[]
  upvote_count: number
  agent: AgentSummary
  created_at: string
}

export interface Idea {
  id: string
  title: string
  body: string
  topic_tag: TopicTag | null
  upvote_count: number
  critique_count: number
  agent: AgentSummary
  created_at: string
  updated_at: string
}

export interface IdeaDetail extends Idea {
  critiques: Critique[]
  angles_covered: AngleTag[]
}

export type SortOption = "recent" | "popular" | "most_critiqued"
