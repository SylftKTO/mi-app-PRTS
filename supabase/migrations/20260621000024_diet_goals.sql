-- Metas de macros por cuenta (módulo Dieta). Una fila por usuario (PK user_id).
-- kcal se almacena ya calculada (P·4 + C·4 + G·9) para lectura directa (p. ej. Pocket).
-- Degradación total: si no hay fila o la tabla no existe, el cliente usa los defaults.

create table public.diet_goals (
  user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  kcal numeric(6,1) not null default 2135,
  protein_g numeric(5,1) not null default 110,
  carbs_g numeric(5,1) not null default 300,
  fat_g numeric(5,1) not null default 55,
  updated_at timestamptz not null default now()
);

alter table public.diet_goals enable row level security;

create policy "owner_all" on public.diet_goals
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
