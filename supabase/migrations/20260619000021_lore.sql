-- Elfie · Archivo interno / Lore (Fase 8.3a).
-- Diario técnico/codex de PRTS: entradas con código PRTS-NNN. Sirve de identidad
-- y memoria de largo plazo de Elfie (en escritorio se indexan en LanceDB para que
-- las recuerde). RLS owner_all. TZ America/Mexico_City.

create table public.lore_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  code text not null,                       -- "PRTS-001"
  title text not null default '',
  body text not null default '',
  kind text not null default 'diario'       -- sistema | elfie | diario
    check (kind in ('sistema', 'elfie', 'diario')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, code)
);

create index lore_entries_user_idx on public.lore_entries (user_id, code);

alter table public.lore_entries enable row level security;

create policy "owner_all" on public.lore_entries
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
