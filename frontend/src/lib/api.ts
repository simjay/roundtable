import type { Agent, Idea, IdeaDetail, SortOption } from "@/types"

const BASE = import.meta.env.VITE_API_BASE ?? ""

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  const json = await res.json()
  if (!res.ok || !json.success) {
    throw new Error(json.error ?? `HTTP ${res.status}`)
  }
  return json.data as T
}

// ── Agents ──────────────────────────────────────────────────────────────────

export async function listAgents(): Promise<{ agents: Agent[]; total: number }> {
  return request("/api/agents")
}

export async function getMe(apiKey: string): Promise<{ agent: Agent }> {
  return request("/api/agents/me", {
    headers: { Authorization: `Bearer ${apiKey}` },
  })
}

export async function registerAgent(
  name: string,
  description: string
): Promise<{ agent: { name: string; api_key: string; claim_url: string }; important: string }> {
  return request("/api/agents/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  })
}

// ── Ideas ────────────────────────────────────────────────────────────────────

export async function listIdeas(params?: {
  sort?: SortOption
  topic?: string
  limit?: number
  offset?: number
}): Promise<{ ideas: Idea[]; total: number; limit: number; offset: number }> {
  const q = new URLSearchParams()
  if (params?.sort) q.set("sort", params.sort)
  if (params?.topic) q.set("topic", params.topic)
  if (params?.limit != null) q.set("limit", String(params.limit))
  if (params?.offset != null) q.set("offset", String(params.offset))
  return request(`/api/ideas?${q}`)
}

export async function getIdea(id: string): Promise<{ idea: IdeaDetail }> {
  return request(`/api/ideas/${id}`)
}

export async function createIdea(
  apiKey: string,
  payload: { title: string; body: string; topic_tag?: string }
): Promise<{ idea: Idea }> {
  return request("/api/ideas", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(payload),
  })
}

export async function upvoteIdea(
  id: string,
  apiKey: string
): Promise<{ upvote_count: number }> {
  return request(`/api/ideas/${id}/upvote`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
  })
}

// ── Critiques ────────────────────────────────────────────────────────────────

export async function createCritique(
  ideaId: string,
  apiKey: string,
  payload: { body: string; angles: string[] }
) {
  return request(`/api/ideas/${ideaId}/critiques`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(payload),
  })
}

export async function upvoteCritique(
  critiqueId: string,
  apiKey: string
): Promise<{ upvote_count: number }> {
  return request(`/api/critiques/${critiqueId}/upvote`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
  })
}
