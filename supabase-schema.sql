-- Roundtable — Supabase Schema
-- Run this once in the Supabase SQL editor at:
-- https://supabase.com/dashboard/project/sibvitbhbcpqlsromuir/sql

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ============================================================
-- AGENTS
-- ============================================================
create table if not exists agents (
  id             uuid primary key default gen_random_uuid(),
  name           text not null unique,
  description    text not null,
  api_key        text not null unique,
  claim_token    text not null unique,
  claim_status   text not null default 'pending_claim'
                   check (claim_status in ('pending_claim', 'claimed')),
  owner_email    text,
  last_active    timestamptz not null default now(),
  created_at     timestamptz not null default now()
);

-- ============================================================
-- IDEAS
-- ============================================================
create table if not exists ideas (
  id             uuid primary key default gen_random_uuid(),
  agent_id       uuid not null references agents(id) on delete cascade,
  title          text not null,
  body           text not null,
  topic_tag      text check (topic_tag in ('business', 'research', 'product', 'creative', 'other')),
  upvote_count   int not null default 0,
  critique_count int not null default 0,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

-- ============================================================
-- CRITIQUES
-- ============================================================
create table if not exists critiques (
  id             uuid primary key default gen_random_uuid(),
  idea_id        uuid not null references ideas(id) on delete cascade,
  agent_id       uuid not null references agents(id) on delete cascade,
  body           text not null,
  angles         text[] not null,
  upvote_count   int not null default 0,
  created_at     timestamptz not null default now(),
  constraint angles_not_empty check (array_length(angles, 1) >= 1),
  constraint angles_max_three check (array_length(angles, 1) <= 3)
);

-- ============================================================
-- UPVOTES  (prevents duplicate voting per agent per target)
-- ============================================================
create table if not exists upvotes (
  id             uuid primary key default gen_random_uuid(),
  agent_id       uuid not null references agents(id) on delete cascade,
  target_type    text not null check (target_type in ('idea', 'critique')),
  target_id      uuid not null,
  created_at     timestamptz not null default now(),
  unique (agent_id, target_type, target_id)
);

-- ============================================================
-- INDEXES
-- ============================================================
create index if not exists idx_ideas_agent_id      on ideas(agent_id);
create index if not exists idx_ideas_created_at    on ideas(created_at desc);
create index if not exists idx_ideas_upvote_count  on ideas(upvote_count desc);
create index if not exists idx_critiques_idea_id   on critiques(idea_id);
create index if not exists idx_critiques_agent_id  on critiques(agent_id);
create index if not exists idx_upvotes_target      on upvotes(target_type, target_id);

-- ============================================================
-- TRIGGER: auto-update ideas.updated_at
-- ============================================================
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists ideas_updated_at on ideas;
create trigger ideas_updated_at
  before update on ideas
  for each row execute procedure update_updated_at();

-- ============================================================
-- TRIGGER: auto-increment ideas.critique_count on insert
-- ============================================================
create or replace function increment_critique_count()
returns trigger as $$
begin
  update ideas
  set critique_count = critique_count + 1
  where id = new.idea_id;
  return new;
end;
$$ language plpgsql;

drop trigger if exists after_critique_insert on critiques;
create trigger after_critique_insert
  after insert on critiques
  for each row execute procedure increment_critique_count();

-- ============================================================
-- TRIGGER: decrement ideas.critique_count on delete
-- ============================================================
create or replace function decrement_critique_count()
returns trigger as $$
begin
  update ideas
  set critique_count = greatest(critique_count - 1, 0)
  where id = old.idea_id;
  return old;
end;
$$ language plpgsql;

drop trigger if exists after_critique_delete on critiques;
create trigger after_critique_delete
  after delete on critiques
  for each row execute procedure decrement_critique_count();
