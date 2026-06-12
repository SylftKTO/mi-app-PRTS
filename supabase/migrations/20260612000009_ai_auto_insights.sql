-- Fase 4.3 (acciones automáticas) + 4.4 (insights)
-- Estilo existente: user_id default auth.uid(), RLS owner_all, TZ America/Mexico_City.

-- ============================================================
-- 1) 4.3 — Auto-aplicación por módulo de alta confianza
-- ============================================================
-- auto_modules: qué módulos se aplican sin confirmar, p. ej. {"tareas": true}
-- auto_threshold: confianza mínima para auto-aplicar (más alto que el 0.8 de sugerir)
alter table public.ai_settings
  add column if not exists auto_modules jsonb not null default '{}'::jsonb,
  add column if not exists auto_threshold numeric(3,2) not null default 0.90;

alter table public.ai_settings
  drop constraint if exists ai_settings_auto_threshold_check;
alter table public.ai_settings
  add constraint ai_settings_auto_threshold_check check (auto_threshold between 0.50 and 1.00);

-- Acierto del inbox (datos de 4.1 → decidir qué automatizar).
-- procesada  = el usuario confirmó la sugerencia (result.module)
-- descartada = el usuario rechazó la sugerencia (result.suggested_module, lo guarda el cliente)
create or replace function public.ai_inbox_accuracy()
returns table (module text, confirmadas bigint, rechazadas bigint)
language sql stable as $$
  select coalesce(result->>'module', result->>'suggested_module') as module,
         count(*) filter (where status = 'procesada')  as confirmadas,
         count(*) filter (where status = 'descartada') as rechazadas
  from public.inbox_entries
  where user_id = auth.uid() and result is not null
  group by 1
  order by 1;
$$;
grant execute on function public.ai_inbox_accuracy() to authenticated;

-- ============================================================
-- 2) 4.4 — Insights (patrones/correlaciones sobre ~1 mes de datos)
-- ============================================================
create table if not exists public.ai_insights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  period_start date not null,
  period_end date not null,
  items jsonb not null,                      -- [{kind, title, detail}]
  model text,
  prompt_version text,
  source jsonb,                              -- agregados usados, para auditoría
  created_at timestamptz not null default now(),
  unique (user_id, period_end)
);
create index if not exists idx_ai_insights_latest on public.ai_insights (user_id, period_end desc);

alter table public.ai_insights enable row level security;
do $$ begin
  create policy "owner_all" on public.ai_insights
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
exception when duplicate_object then null; end $$;
