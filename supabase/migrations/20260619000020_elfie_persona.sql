-- Elfie · Perfil de personalidad estructurado (Fase 8.3b).
-- Amplía elfie_config con un perfil por ejes (iniciativa, detalle, confirmaciones,
-- arquetipo libre) que el cliente compone en el tono efectivo del system prompt.
-- jsonb para no añadir una columna por eje y poder crecer sin migraciones.

alter table public.elfie_config
  add column if not exists persona jsonb not null default '{}'::jsonb;

comment on column public.elfie_config.persona is
  'Perfil de personalidad: {iniciativa, detalle, confirmaciones, desc}. Lo compone el cliente (elfie-config.js) en tone().';
