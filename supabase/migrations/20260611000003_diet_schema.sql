-- Módulo Dieta: banco de comidas personales + registros de consumo
-- Targets (doc 12): 2,135 kcal · 110 P · 300 C · 55 G en 4 comidas

-- Banco personal de comidas frecuentes (macros precalculados, registro en un toque)
create table public.foods (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  kcal numeric(6,1) not null,
  protein_g numeric(5,1) not null default 0,
  carbs_g numeric(5,1) not null default 0,
  fat_g numeric(5,1) not null default 0,
  created_at timestamptz not null default now(),
  unique (user_id, name)
);

-- Registro de consumo real por comida
create table public.meal_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  log_date date not null default (now() at time zone 'America/Mexico_City')::date,
  meal text not null check (meal in ('desayuno', 'comida', 'pregym', 'cena', 'snack')),
  food_id uuid references public.foods(id) on delete set null,
  name text not null,
  kcal numeric(6,1) not null,
  protein_g numeric(5,1) not null default 0,
  carbs_g numeric(5,1) not null default 0,
  fat_g numeric(5,1) not null default 0,
  created_at timestamptz not null default now()
);

create index idx_meal_logs_date on public.meal_logs (user_id, log_date desc);

alter table public.foods enable row level security;
alter table public.meal_logs enable row level security;

create policy "owner_all" on public.foods
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.meal_logs
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
