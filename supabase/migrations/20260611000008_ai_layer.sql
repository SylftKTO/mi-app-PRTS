-- Fase 4.0 — Capa de IA: infraestructura mínima
-- 1) Tablas: ai_calls (costos/tokens), daily_briefings (briefing pre-generado), ai_settings (presupuesto)
-- 2) ai_spend_month(): gasto del mes en curso para el tope
-- 3) Refactor de dashboard_brief() → dashboard_brief_for(uid) SECURITY DEFINER
--    para poder generar el briefing desde una Edge Function (service role, sin auth.uid()).

-- ============================================================
-- 1) TABLAS
-- ============================================================
create table if not exists public.ai_calls (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,  -- la Edge Function lo setea explícito
  agent text not null,                       -- 'inbox' | 'briefing' | 'command' | 'insights'
  prompt_version text not null,
  model text not null,
  input_tokens int not null default 0,
  output_tokens int not null default 0,
  cost_usd numeric(10,6) not null default 0,
  latency_ms int,
  status text not null default 'ok' check (status in ('ok','error','degraded')),
  error text,
  ref_table text,
  ref_id uuid,
  created_at timestamptz not null default now()
);
create index if not exists idx_ai_calls_month on public.ai_calls (user_id, created_at desc);

create table if not exists public.daily_briefings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  brief_date date not null default (now() at time zone 'America/Mexico_City')::date,
  text text not null,
  model text,
  prompt_version text,
  source jsonb,
  created_at timestamptz not null default now(),
  unique (user_id, brief_date)
);

create table if not exists public.ai_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  monthly_cap_usd numeric(8,2) not null default 5.00,
  enabled boolean not null default true,
  updated_at timestamptz not null default now()
);

-- Semilla para los usuarios existentes (single-user en la práctica)
insert into public.ai_settings (user_id)
  select id from auth.users on conflict (user_id) do nothing;

-- ============================================================
-- 2) RLS
-- ============================================================
alter table public.ai_calls        enable row level security;
alter table public.daily_briefings enable row level security;
alter table public.ai_settings     enable row level security;

do $$ begin
  create policy "owner_all" on public.ai_calls
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "owner_all" on public.daily_briefings
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "owner_all" on public.ai_settings
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;

-- ============================================================
-- 3) Gasto del mes en curso (para el tope mensual, lado cliente)
-- ============================================================
create or replace function public.ai_spend_month()
returns numeric
language sql
stable
as $$
  select coalesce(sum(cost_usd), 0)
  from public.ai_calls
  where user_id = auth.uid()
    and created_at >= date_trunc('month', now() at time zone 'America/Mexico_City');
$$;
grant execute on function public.ai_spend_month() to authenticated;

-- ============================================================
-- 4) dashboard_brief_for(uid): mismo cálculo agregado que dashboard_brief()
--    pero recibe el usuario por parámetro y corre como SECURITY DEFINER,
--    para poder llamarse desde la Edge Function con service role.
-- ============================================================
create or replace function public.dashboard_brief_for(p_user uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
declare
  uid uuid := p_user;
  today date := (now() at time zone 'America/Mexico_City')::date;
  wd int := extract(dow from today)::int;   -- 0 = domingo (convención JS)
  week_start date := today - wd;
  result jsonb;
  gym_routine text;
  gym_sets_today int;
  gym_sessions_week int;
  gym_last date;
  gym_has_routine boolean;
  gym_logged boolean;
begin
  select rd.name into gym_routine
    from public.routine_days rd
    where rd.user_id = uid and rd.weekday = wd;
  gym_has_routine := gym_routine is not null;

  select count(*) into gym_sessions_week
    from public.workout_sessions
    where user_id = uid and session_date >= week_start and session_date <= today;

  select max(session_date) into gym_last
    from public.workout_sessions where user_id = uid;

  select count(*) into gym_sets_today
    from public.workout_sets ws
    join public.workout_sessions s on s.id = ws.session_id
    where ws.user_id = uid and s.session_date = today;

  gym_logged := exists (
    select 1 from public.workout_sessions
    where user_id = uid and session_date = today);

  result := jsonb_build_object(
    'fecha', today,
    'weekday', wd,
    'gym', jsonb_build_object(
      'routine', gym_routine,
      'has_routine_today', gym_has_routine,
      'sets_today', gym_sets_today,
      'logged_today', gym_logged,
      'sessions_week', gym_sessions_week,
      'last_session', gym_last,
      'streak_at_risk', (gym_has_routine and not gym_logged)
    ),
    'tasks', (
      select jsonb_build_object(
        'pending', count(*) filter (where status = 'pendiente'),
        'completed_week', count(*) filter (where status = 'completada' and completed_at >= week_start),
        'urgent', coalesce((
          select jsonb_agg(jsonb_build_object(
            'id', id, 'title', title, 'origin', origin, 'priority', priority, 'deadline', deadline
          ) order by deadline)
          from public.tasks t2
          where t2.user_id = uid and t2.status = 'pendiente'
            and t2.deadline is not null and t2.deadline <= today + 1
        ), '[]'::jsonb),
        'next', coalesce((
          select jsonb_agg(x) from (
            select jsonb_build_object(
              'id', id, 'title', title, 'origin', origin, 'priority', priority, 'deadline', deadline
            ) as x
            from public.tasks t3
            where t3.user_id = uid and t3.status = 'pendiente'
            order by deadline asc nulls last, created_at asc
            limit 6
          ) s
        ), '[]'::jsonb)
      )
      from public.tasks
      where user_id = uid and status in ('pendiente', 'completada')
    ),
    'projects', (
      select jsonb_build_object(
        'active', count(*) filter (where status = 'activo'),
        'due_soon', coalesce((
          select jsonb_agg(jsonb_build_object(
            'id', id, 'name', name, 'due_date', due_date
          ) order by due_date)
          from public.projects p2
          where p2.user_id = uid and p2.status = 'activo'
            and p2.due_date is not null and p2.due_date <= today + 7
        ), '[]'::jsonb)
      )
      from public.projects where user_id = uid
    ),
    'week_today', coalesce((
      select jsonb_agg(jsonb_build_object(
        'label', label, 'role', role, 'start', start_time, 'end', end_time
      ) order by start_time)
      from public.week_blocks where user_id = uid and weekday = wd
    ), '[]'::jsonb),
    'diet', (
      select jsonb_build_object(
        'kcal', coalesce(sum(kcal), 0),
        'protein', coalesce(sum(protein_g), 0),
        'carbs', coalesce(sum(carbs_g), 0),
        'fat', coalesce(sum(fat_g), 0),
        'logged', count(*) > 0
      )
      from public.meal_logs where user_id = uid and log_date = today
    ),
    'notes', (
      select jsonb_build_object(
        'open_doubts', count(*) filter (where coalesce(trim(doubts), '') <> ''),
        'total', count(*)
      )
      from public.notes where user_id = uid
    )
  );

  result := result || jsonb_build_object('heat', jsonb_build_object(
    'tareas',    (result->'tasks'->>'pending')::int,
    'proyectos', jsonb_array_length(result->'projects'->'due_soon'),
    'gym',       case when (result->'gym'->>'streak_at_risk')::boolean then 1 else 0 end,
    'dieta',     case when (result->'diet'->>'logged')::boolean then 0 else 1 end,
    'apuntes',   (result->'notes'->>'open_doubts')::int,
    'semana',    jsonb_array_length(result->'week_today')
  ));

  return result;
end;
$$;
grant execute on function public.dashboard_brief_for(uuid) to authenticated, service_role;

-- dashboard_brief() ahora delega (mantiene compatibilidad con el cliente)
create or replace function public.dashboard_brief()
returns jsonb
language sql
stable
as $$
  select public.dashboard_brief_for(auth.uid());
$$;
grant execute on function public.dashboard_brief() to authenticated;
