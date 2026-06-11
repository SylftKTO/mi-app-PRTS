-- Módulo Gym: esquema inicial
-- Modelo: ejercicios (catálogo) → días de rutina → ejercicios por día
--         sesiones de entrenamiento → sets registrados (peso × reps)

-- Catálogo de ejercicios
create table public.exercises (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  unique (user_id, name)
);

-- Días de rutina (Leg A, Push A, ...)
create table public.routine_days (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  weekday smallint not null check (weekday between 0 and 6), -- 0 = domingo
  name text not null,
  unique (user_id, weekday)
);

-- Ejercicios asignados a cada día de rutina
create table public.routine_exercises (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  routine_day_id uuid not null references public.routine_days(id) on delete cascade,
  exercise_id uuid not null references public.exercises(id) on delete cascade,
  position smallint not null,
  target_sets smallint not null,
  rep_min smallint not null,
  rep_max smallint not null
);

-- Sesiones de entrenamiento (una por día asistido)
create table public.workout_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  routine_day_id uuid references public.routine_days(id) on delete set null,
  session_date date not null default (now() at time zone 'America/Mexico_City')::date,
  notes text,
  created_at timestamptz not null default now(),
  unique (user_id, session_date)
);

-- Sets registrados
create table public.workout_sets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  session_id uuid not null references public.workout_sessions(id) on delete cascade,
  exercise_id uuid not null references public.exercises(id) on delete cascade,
  set_number smallint not null,
  weight_kg numeric(5,1) not null,
  reps smallint not null,
  created_at timestamptz not null default now()
);

create index idx_sets_exercise on public.workout_sets (user_id, exercise_id, created_at desc);
create index idx_sessions_date on public.workout_sessions (user_id, session_date desc);

-- Row Level Security: solo el propietario accede a sus filas
alter table public.exercises enable row level security;
alter table public.routine_days enable row level security;
alter table public.routine_exercises enable row level security;
alter table public.workout_sessions enable row level security;
alter table public.workout_sets enable row level security;

create policy "owner_all" on public.exercises
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.routine_days
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.routine_exercises
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.workout_sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.workout_sets
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
