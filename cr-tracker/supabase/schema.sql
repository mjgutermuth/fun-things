-- cr_sync table: account-based sync (Supabase Auth)
--
-- Run this once in the Supabase SQL editor for this project
-- (https://wkqjgakouqjvfoyseaui.supabase.co) to move cr_sync from the
-- old anonymous `sync_id` scheme to real per-account rows keyed by
-- the logged-in user's auth.uid().
--
-- Safe to re-run: every statement is idempotent.

alter table cr_sync add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- One row per account. Required for the app's upsert(..., { onConflict: 'user_id' }).
create unique index if not exists cr_sync_user_id_key on cr_sync (user_id) where user_id is not null;

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
