-- Elfie Chat (Fase 7.1): chat conversacional con memoria y personalidad.
-- Dos tablas: sesiones de chat + mensajes. La memoria de largo plazo (hechos
-- durables) vive on-device en LanceDB (chat.py), NO aquí: estas tablas guardan el
-- historial literal de la conversación, sincronizado entre desktop y web.
-- RLS owner_all (auth.uid() = user_id). TZ America/Mexico_City por defecto.

create table public.elfie_chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  title text not null default 'Conversación',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.elfie_chat_messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  session_id uuid not null references public.elfie_chat_sessions(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create index elfie_chat_messages_session_idx
  on public.elfie_chat_messages (session_id, created_at);
create index elfie_chat_sessions_user_idx
  on public.elfie_chat_sessions (user_id, updated_at desc);

alter table public.elfie_chat_sessions enable row level security;
alter table public.elfie_chat_messages enable row level security;

create policy "owner_all" on public.elfie_chat_sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owner_all" on public.elfie_chat_messages
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
