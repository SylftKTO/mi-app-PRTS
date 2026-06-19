-- Elfie Desktop (Fase 5): Routine Engine Visual — rutinas configurables desde la UI.
-- steps: [{action, params, delay_ms}] ejecutadas en secuencia por el cliente.
create table public.routines (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  trigger_phrase text,                   -- "modo estudio" (voz)
  shortcut text,                         -- "Ctrl+Shift+E" (atajo global)
  steps jsonb not null default '[]'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index idx_routines_user on public.routines (user_id);

alter table public.routines enable row level security;

create policy "owner_all" on public.routines
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
