-- Elfie Desktop (Fase 2/5): historial de métricas del sistema (para gráficas de tendencia).
-- Muestreo esporádico (no cada 3s) para no saturar; el live va por eventos Tauri.
create table public.system_metrics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  cpu_percent real,
  ram_used_gb real,
  gpu_percent real,
  gpu_vram_used_gb real,
  gpu_temp_c real,
  gpu_power_w real,
  recorded_at timestamptz not null default now()
);

create index idx_system_metrics_user_when on public.system_metrics (user_id, recorded_at desc);

alter table public.system_metrics enable row level security;

create policy "owner_all" on public.system_metrics
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
