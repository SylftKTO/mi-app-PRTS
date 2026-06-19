-- Elfie Desktop (Fase 6, tabla creada ya): perfiles de voz clonados (XTTS v2 / Fish Speech).
create table public.voice_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  engine text not null,                  -- xtts | fish | ...
  reference_audio_url text,              -- audio de referencia para clonar
  config jsonb,
  is_active boolean not null default false,
  created_at timestamptz not null default now()
);

create index idx_voice_profiles_user on public.voice_profiles (user_id);

alter table public.voice_profiles enable row level security;

create policy "owner_all" on public.voice_profiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
