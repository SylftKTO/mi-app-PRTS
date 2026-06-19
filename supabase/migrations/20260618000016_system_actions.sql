-- Elfie Desktop (Fase 2): log de acciones del sistema operativo (abrir apps, volumen, etc.).
create table public.system_actions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  action_type text not null,             -- open_app | set_volume | screenshot | ...
  payload jsonb,
  executed_at timestamptz not null default now()
);

create index idx_system_actions_user_when on public.system_actions (user_id, executed_at desc);

alter table public.system_actions enable row level security;

create policy "owner_all" on public.system_actions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
