-- Elfie · Bitácora de protocolos (Fase 9.3).
-- Cada ejecución de una rutina/protocolo (desde voz, gestor o la mascota) deja un
-- registro: nombre, pasos totales/ejecutados y estado. La mascota narra inicio/cierre
-- y muestra los pasos; aquí queda la traza durable. RLS owner_all. TZ America/Mexico_City.
-- Degradación total: el cliente también guarda en localStorage, así que funciona sin esta tabla.

create table public.protocol_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null default '',
  steps_total int not null default 0,
  steps_done int not null default 0,
  status text not null default 'completado'      -- completado | parcial | error
    check (status in ('completado', 'parcial', 'error')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  created_at timestamptz not null default now()
);

create index protocol_log_user_idx on public.protocol_log (user_id, started_at desc);

alter table public.protocol_log enable row level security;

create policy "owner_all" on public.protocol_log
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
