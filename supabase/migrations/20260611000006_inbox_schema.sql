-- Captura universal (bandeja de entrada para la capa IA, Fase 4)
-- El usuario escribe texto libre; PRTS lo procesará y completará el registro
-- en el módulo correspondiente (tarea, gasto, apunte, entrenamiento, recordatorio…).

create table public.inbox_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  raw_text text not null,
  status text not null default 'pendiente' check (status in ('pendiente', 'procesada', 'descartada')),
  processed_at timestamptz,
  result jsonb,                       -- reservado: qué creó la IA (módulo, id destino, resumen)
  created_at timestamptz not null default now()
);

create index idx_inbox_pending on public.inbox_entries (user_id, status, created_at desc);

alter table public.inbox_entries enable row level security;

create policy "owner_all" on public.inbox_entries
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
