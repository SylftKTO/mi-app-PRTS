-- Módulo Recordatorios (Fase 5): avisos con hora.
-- PRTS es la fuente de verdad; la notificación al celular la entrega Google
-- Calendar (evento con recordatorio). google_event_id liga la fila con su evento.

create table public.reminders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  title text not null,
  notes text,
  remind_at timestamptz not null,
  lead_minutes int not null default 0,          -- avisar N minutos antes de remind_at
  status text not null default 'pendiente' check (status in ('pendiente', 'hecho', 'cancelado')),
  google_event_id text,                          -- evento en Google Calendar (null = no sincronizado)
  created_at timestamptz not null default now()
);

create index idx_reminders_user_when on public.reminders (user_id, remind_at);

alter table public.reminders enable row level security;

create policy "owner_all" on public.reminders
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
