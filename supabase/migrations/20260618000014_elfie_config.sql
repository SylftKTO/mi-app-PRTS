-- Elfie Desktop (Fase 4): configuración de personalidad, voz y modelo LLM local.
-- Una fila por usuario (PK = user_id). Sincronizada entre desktop y web.

create table public.elfie_config (
  user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  personality text not null default 'profesional'
    check (personality in ('profesional', 'casual', 'silenciosa', 'tecnica', 'nocturna')),
  voice_engine text not null default 'kokoro'
    check (voice_engine in ('kokoro', 'piper', 'xtts', 'edge', 'elevenlabs', 'navegador')),
  voice_name text not null default 'ef_dora',     -- voz dentro del motor
  voice_speed real not null default 1.0,
  verbosity text not null default 'concisa'
    check (verbosity in ('minima', 'concisa', 'media', 'detallada')),
  tts_enabled boolean not null default true,
  local_llm_model text not null default 'phi3.5', -- modelo Ollama por defecto
  updated_at timestamptz not null default now()
);

alter table public.elfie_config enable row level security;

create policy "owner_all" on public.elfie_config
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
