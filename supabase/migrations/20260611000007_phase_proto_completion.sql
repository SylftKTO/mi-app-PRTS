-- Cierre de la fase prototípica
-- 1) Grupo muscular en el catálogo de ejercicios (gráficas por grupo)
-- 2) Registro de peso corporal (tendencia + media móvil)
-- 3) Búsqueda full-text en apuntes (tsvector + GIN + RPC)
-- 4) Capa de datos agregada del dashboard (un solo round-trip)

-- ============================================================
-- 1) GRUPO MUSCULAR
-- ============================================================
alter table public.exercises add column if not exists muscle_group text;

-- Semilla para los ejercicios de la rutina actual (por nombre)
update public.exercises set muscle_group = case name
  when 'Abductores'        then 'Glúteo'
  when 'Extensiones'       then 'Cuádriceps'
  when 'Péndulo / Hack'    then 'Cuádriceps'
  when 'Femoral'           then 'Femoral'
  when 'Peso muerto'       then 'Femoral'
  when 'Hip thrust'        then 'Glúteo'
  when 'Pantorrilla'       then 'Pantorrilla'
  when 'Fondos'            then 'Pecho'
  when 'Pushdowns'         then 'Tríceps'
  when 'Overhead'          then 'Tríceps'
  when 'Peck Deck (negra)' then 'Pecho'
  when 'Press pecho alto'  then 'Pecho'
  when 'Militar'           then 'Hombro'
  when 'Elevaciones'       then 'Hombro'
  when 'Hombro posterior'  then 'Hombro'
  when 'Predicador'        then 'Bíceps'
  when 'Martillo'          then 'Bíceps'
  when 'Jalón al pecho'    then 'Espalda'
  when 'Jalón cerrado'     then 'Espalda'
  when 'Remo T'            then 'Espalda'
  when 'Gatitos'           then 'Espalda'
  else muscle_group
end
where muscle_group is null;

-- ============================================================
-- 2) PESO CORPORAL
-- ============================================================
create table if not exists public.body_weights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  measured_on date not null default (now() at time zone 'America/Mexico_City')::date,
  weight_kg numeric(5,1) not null check (weight_kg > 0),
  note text,
  created_at timestamptz not null default now(),
  unique (user_id, measured_on)
);
create index if not exists idx_bw_date on public.body_weights (user_id, measured_on);

alter table public.body_weights enable row level security;
do $$ begin
  create policy "owner_all" on public.body_weights
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;

-- ============================================================
-- 3) BÚSQUEDA FULL-TEXT EN APUNTES
-- ============================================================
alter table public.notes add column if not exists fts tsvector
  generated always as (
    to_tsvector('spanish',
      coalesce(subject, '')       || ' ' ||
      coalesce(topic, '')         || ' ' ||
      coalesce(key_concepts, '')  || ' ' ||
      coalesce(formulas, '')      || ' ' ||
      coalesce(doubts, '')        || ' ' ||
      coalesce(connections, '')   || ' ' ||
      coalesce(summary, ''))
  ) stored;
create index if not exists idx_notes_fts on public.notes using gin (fts);

create or replace function public.search_notes(q text)
returns setof public.notes
language sql
stable
as $$
  select *
  from public.notes
  where user_id = auth.uid()
    and fts @@ websearch_to_tsquery('spanish', q)
  order by ts_rank(fts, websearch_to_tsquery('spanish', q)) desc,
           note_date desc;
$$;
grant execute on function public.search_notes(text) to authenticated;

-- ============================================================
-- 4) CAPA AGREGADA DEL DASHBOARD
--    Un solo llamado devuelve todo lo que pinta el dashboard:
--    gym de hoy, racha, tareas urgentes, proyectos por entregar,
--    bloques de hoy, dieta de hoy, dudas abiertas y "calor" por módulo.
-- ============================================================
create or replace function public.dashboard_brief()
returns jsonb
language plpgsql
stable
as $$
declare
  uid uuid := auth.uid();
  today date := (now() at time zone 'America/Mexico_City')::date;
  wd int := extract(dow from today)::int;   -- 0 = domingo (convención JS)
  week_start date := today - wd;            -- domingo de esta semana
  result jsonb;
  gym_routine text;
  gym_sets_today int;
  gym_sessions_week int;
  gym_last date;
  gym_has_routine boolean;
  gym_logged boolean;
begin
  -- GYM
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

  -- "Calor" del mapa: cuántos pendientes pesan en cada módulo
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
grant execute on function public.dashboard_brief() to authenticated;
