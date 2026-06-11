-- Módulo Apuntes: plantilla de 5 campos (doc sección 7)
-- conceptos clave, fórmulas, dudas, conexiones, resumen en 3 líneas

create table public.notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  subject text not null default '',       -- materia
  topic text not null default '',         -- tema
  note_date date not null default (now() at time zone 'America/Mexico_City')::date,
  key_concepts text not null default '',
  formulas text not null default '',
  doubts text not null default '',        -- las dudas son del estudiante, no del modelo
  connections text not null default '',
  summary text not null default '',       -- resumen en 3 líneas
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_notes_date on public.notes (user_id, note_date desc);

alter table public.notes enable row level security;

create policy "owner_all" on public.notes
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
