-- Módulo Proyectos (doc 6): proyecto + subtareas, % calculado en cliente
-- Módulo Semana (doc 4): plantilla semanal de bloques de tiempo por rol

-- ---------- PROYECTOS ----------
create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  subject text,                                          -- materia
  due_date date,                                         -- entrega final
  status text not null default 'activo' check (status in ('activo', 'completado', 'archivado')),
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.project_subtasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  title text not null,
  done boolean not null default false,
  position int not null default 0,
  created_at timestamptz not null default now()
);

create index idx_projects_active on public.projects (user_id, status, due_date);
create index idx_subtasks_project on public.project_subtasks (project_id, position);

alter table public.projects enable row level security;
alter table public.project_subtasks enable row level security;

create policy "owner_all" on public.projects
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.project_subtasks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------- SEMANA (plantilla de bloques recurrentes) ----------
-- weekday: convención JS getDay() → 0 = domingo … 6 = sábado
create table public.week_blocks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  weekday int not null check (weekday between 0 and 6),
  start_time time not null,
  end_time time not null,
  role text not null check (role in ('escuela', 'gym', 'wolves', 'levelup', 'personal')),
  label text not null,
  created_at timestamptz not null default now(),
  check (end_time > start_time)
);

create index idx_week_blocks on public.week_blocks (user_id, weekday, start_time);

alter table public.week_blocks enable row level security;

create policy "owner_all" on public.week_blocks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
