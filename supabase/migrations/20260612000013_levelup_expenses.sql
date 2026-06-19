-- LevelUp · Gastos de operación (separados de los sueldos, que se calculan de
-- los maestros). Clases muestra, marketing, materiales/libros, productos
-- visuales, renta, etc. Migración independiente: aplica corrida o no la ..0012.

create table public.levelup_expenses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  entry_date date not null default (now() at time zone 'America/Mexico_City')::date,
  category text not null,                                 -- clases_muestra · marketing · materiales · visuales · renta · otros
  concept text,
  amount numeric(10,2) not null check (amount > 0),
  notes text,
  created_at timestamptz not null default now()
);

create index idx_lu_expenses_user_date on public.levelup_expenses (user_id, entry_date desc);

alter table public.levelup_expenses enable row level security;

create policy "owner_all" on public.levelup_expenses
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
