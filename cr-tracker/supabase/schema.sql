-- cr_sync table: account-based sync (Supabase Auth)
--
-- Run this once in the Supabase SQL editor for this project
-- (https://wkqjgakouqjvfoyseaui.supabase.co) to move cr_sync from the
-- old anonymous `sync_id` scheme to real per-account rows keyed by
-- the logged-in user's auth.uid().
--
-- Safe to re-run: every statement is idempotent.

alter table cr_sync add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- sync_id is the table's primary key (NOT NULL, and Postgres won't let you
-- drop NOT NULL from a PK column - don't try). The app now just writes the
-- user's own id into sync_id too on every save, so it stays populated
-- without needing a schema change. It's otherwise unused going forward.

-- One row per account. Required for the app's upsert(..., { onConflict: 'user_id' }).
-- Must NOT be a partial index (no `where user_id is not null`) - Postgres
-- won't use a partial index as an ON CONFLICT arbiter unless the query
-- repeats the same WHERE clause. A plain unique index works fine here:
-- NULL user_id values (the old anonymous rows) never count as duplicates
-- of each other under a unique index.
create unique index if not exists cr_sync_user_id_key on cr_sync (user_id);

alter table cr_sync enable row level security;

drop policy if exists "select own sync" on cr_sync;
create policy "select own sync" on cr_sync
    for select using (auth.uid() = user_id);

drop policy if exists "insert own sync" on cr_sync;
create policy "insert own sync" on cr_sync
    for insert with check (auth.uid() = user_id);

drop policy if exists "update own sync" on cr_sync;
create policy "update own sync" on cr_sync
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Old rows keyed only by the anonymous sync_id (no user_id) are left in place
-- but are now unreachable under RLS since nothing queries by sync_id anymore.
-- Safe to delete manually later once you've confirmed the new login-based
-- sync has your data on every device: delete from cr_sync where user_id is null;

-- admins table: marks which auth.users account(s) may write episode
-- corrections (see episode_overrides below). Deliberately holds nothing but
-- an opaque user_id - no email, no name - so this file (and this public
-- repo's history) never contains anything identifying. To grant yourself
-- access, run this ONCE directly in the Supabase SQL editor - do not add it
-- to this file or commit it anywhere:
--
--   insert into admins (user_id)
--   select id from auth.users where email = 'your-email-here'
--   on conflict do nothing;

create table if not exists admins (
    user_id uuid primary key references auth.users(id) on delete cascade
);

alter table admins enable row level security;

-- A signed-in user may check only their OWN membership (the app uses this to
-- decide whether to show Edit Mode at all) - never the full admin list.
drop policy if exists "check own admin status" on admins;
create policy "check own admin status" on admins
    for select using (auth.uid() = user_id);

-- episode_overrides table: manual corrections to scraped episode data made
-- from the tracker's "Edit Mode", applied as a display-layer patch over the
-- CSV rather than editing it directly (the frontend is static and has no
-- way to write to a file). Keyed by the CSV's own episode_id.
--
-- Everyone can read overrides, so a corrected title shows for every visitor -
-- only accounts listed in `admins` may write one.

create table if not exists episode_overrides (
    episode_id text primary key,
    show_type text,
    campaign text,
    episode_number text,
    title text,
    updated_at timestamptz not null default now(),
    updated_by uuid references auth.users(id)
);

alter table episode_overrides enable row level security;

drop policy if exists "anyone can read overrides" on episode_overrides;
create policy "anyone can read overrides" on episode_overrides
    for select using (true);

drop policy if exists "admins can insert overrides" on episode_overrides;
create policy "admins can insert overrides" on episode_overrides
    for insert with check (exists (select 1 from admins where user_id = auth.uid()));

drop policy if exists "admins can update overrides" on episode_overrides;
create policy "admins can update overrides" on episode_overrides
    for update using (exists (select 1 from admins where user_id = auth.uid()))
    with check (exists (select 1 from admins where user_id = auth.uid()));

drop policy if exists "admins can delete overrides" on episode_overrides;
create policy "admins can delete overrides" on episode_overrides
    for delete using (exists (select 1 from admins where user_id = auth.uid()));
