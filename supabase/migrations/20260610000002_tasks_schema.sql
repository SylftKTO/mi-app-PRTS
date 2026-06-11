-- Módulo Tareas: esquema inicial
-- Campos según doc 5.3: título, origen, prioridad, deadline, estado, recurrencia, padre

create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  title text not null,
  origin text not null check (origin in ('escuela', 'wolves', 'levelup', 'personal')),
  priority text not null default 'media' check (priority in ('alta', 'media', 'baja')),
  deadline date,
  status text not null default 'pendiente' check (status in ('pendiente', 'completada', 'archivada')),
  completed_at timestamptz,
  recurrence text,                                                    -- reservado (Fase 2+)
  parent_id uuid references public.tasks(id) on delete cascade,      -- reservado: subtareas
  created_at timestamptz not null default now()
);

create index idx_tasks_pending on public.tasks (user_id, status, deadline);

alter table public.tasks enable row level security;

create policy "owner_all" on public.tasks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
