-- Módulo Finanzas: esquema inicial (Fase 5 · básico con gráficas)
-- Modelo: movimientos de dinero (ingreso/gasto) con categoría y fecha.
--         El balance del mes = sum(ingresos) - sum(gastos) sobre entry_date.

create table public.finances (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  entry_date date not null default (now() at time zone 'America/Mexico_City')::date,
  kind text not null check (kind in ('ingreso', 'gasto')),
  category text not null,
  amount numeric(10,2) not null check (amount > 0),
  note text,
  created_at timestamptz not null default now()
);

create index idx_finances_user_date on public.finances (user_id, entry_date desc);

alter table public.finances enable row level security;

create policy "owner_all" on public.finances
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
