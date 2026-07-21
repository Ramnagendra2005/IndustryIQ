-- ==========================================================================
-- IndustryIQ — Supabase persistence schema  (multi-tenant)
-- Run this ONCE in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- Then set SUPABASE_URL and SUPABASE_KEY in .env and restart the backend.
-- The app works fine without any of this — persistence is optional and the
-- demo account always works in-memory even when Supabase is unreachable.
--
-- Safe to re-run: every statement is idempotent. If you created the older
-- single-tenant tables, the ALTERs below upgrade them in place.
-- ==========================================================================

-- Tenants. One row per industry/company; each owns its own knowledge graph.
create table if not exists public.iiq_industries (
  id         text primary key,
  name       text not null,
  join_code  text not null,
  created_at timestamptz not null default now()
);

-- Users. Each belongs to exactly one industry. Email is unique (login key).
create table if not exists public.iiq_users (
  id            text primary key,
  email         text not null unique,
  name          text not null,
  password_hash text not null,
  industry_id   text not null references public.iiq_industries(id),
  role          text not null default 'member',
  created_at    timestamptz not null default now()
);

-- Uploaded documents + their LLM extractions, scoped per industry (the seed
-- corpus is NOT stored; it ships with the app and rebuilds at every boot).
-- PK is "<industry_id>:<doc_id>" so the same doc id can exist per tenant.
create table if not exists public.iiq_documents (
  id           text primary key,
  industry_id  text not null default 'demo',
  doc_id       text,
  title        text not null,
  doc_type     text not null,
  date         text,
  unit         text,
  text         text,
  is_image     boolean not null default false,
  extraction   jsonb not null default '{}'::jsonb,
  pid_geometry jsonb,
  image_b64    text,
  media_type   text,
  created_at   timestamptz not null default now()
);
-- Upgrade an older single-tenant iiq_documents table, if present.
alter table public.iiq_documents add column if not exists industry_id text not null default 'demo';
alter table public.iiq_documents add column if not exists doc_id text;
create index if not exists iiq_documents_industry_idx on public.iiq_documents (industry_id);

-- Copilot conversation context: every question + answer, scoped per industry.
create table if not exists public.iiq_queries (
  id          bigint generated always as identity primary key,
  industry_id text not null default 'demo',
  question    text not null,
  mode        text not null default 'copilot',
  lang        text not null default 'en',
  answer      text,
  confidence  double precision,
  provider    text,
  created_at  timestamptz not null default now()
);
alter table public.iiq_queries add column if not exists industry_id text not null default 'demo';
create index if not exists iiq_queries_industry_idx on public.iiq_queries (industry_id);

-- Row Level Security: enabled, with permissive policies so the backend's
-- anon/service key can read+write. The backend enforces per-industry scoping
-- (every query filters by industry_id); tighten these policies with JWT
-- claims if you expose the anon key directly to browsers.
alter table public.iiq_industries enable row level security;
alter table public.iiq_users      enable row level security;
alter table public.iiq_documents  enable row level security;
alter table public.iiq_queries    enable row level security;

drop policy if exists "iiq_industries_all" on public.iiq_industries;
create policy "iiq_industries_all" on public.iiq_industries for all using (true) with check (true);

drop policy if exists "iiq_users_all" on public.iiq_users;
create policy "iiq_users_all" on public.iiq_users for all using (true) with check (true);

drop policy if exists "iiq_documents_all" on public.iiq_documents;
create policy "iiq_documents_all" on public.iiq_documents for all using (true) with check (true);

drop policy if exists "iiq_queries_all" on public.iiq_queries;
create policy "iiq_queries_all" on public.iiq_queries for all using (true) with check (true);
