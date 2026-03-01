-- HW3 Improvements — run these in the Supabase SQL editor in order.

-- ============================================================
-- 1. Activity log table
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_log (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id     uuid REFERENCES agents(id) ON DELETE CASCADE,
    event_type   text NOT NULL,
    -- 'idea_posted' | 'critique_posted' | 'upvote_cast' | 'agent_registered'
    target_id    uuid,
    target_title text,
    created_at   timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS activity_log_created_at_idx ON activity_log (created_at DESC);
CREATE INDEX IF NOT EXISTS activity_log_agent_id_idx   ON activity_log (agent_id);

-- ============================================================
-- 2. Time-series daily counts RPC (used by GET /api/stats)
-- ============================================================
CREATE OR REPLACE FUNCTION get_daily_counts(tbl text, days_back int)
RETURNS TABLE(day date, count bigint) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY EXECUTE format(
    'SELECT created_at::date AS day, count(*) AS count
     FROM %I
     WHERE created_at >= now() - ($1 || '' days'')::interval
     GROUP BY 1
     ORDER BY 1',
    tbl
  ) USING days_back;
END;
$$;

-- ============================================================
-- 3. Atomic upvote increment RPC (eliminates read-modify-write race)
-- ============================================================
CREATE OR REPLACE FUNCTION increment_upvote(tbl text, row_id uuid)
RETURNS int LANGUAGE plpgsql AS $$
DECLARE
  new_count int;
BEGIN
  EXECUTE format(
    'UPDATE %I SET upvote_count = upvote_count + 1 WHERE id = $1 RETURNING upvote_count',
    tbl
  ) INTO new_count USING row_id;
  RETURN new_count;
END;
$$;
