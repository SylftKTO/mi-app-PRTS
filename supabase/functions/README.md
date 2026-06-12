# PRTS · Edge Functions (capa IA — Fase 4)

Backend de confianza donde viven las llamadas al LLM. La clave del modelo **nunca**
toca el cliente: se queda en los *secrets* de Supabase.

```
_shared/
  llm.ts                 # cliente LLM (Anthropic por defecto) + reintentos + costo
  prompts/briefing.v1.ts # prompt versionado del briefing
generate-briefing/
  index.ts               # genera el briefing diario y lo guarda en daily_briefings
```

> **Proveedor por defecto:** Anthropic (Claude, tier económico). Para cambiarlo se
> toca **solo** `_shared/llm.ts`. El modelo y las tarifas se configuran por entorno.

---

## 1. Requisitos previos

1. Aplicar la migración `20260611000008_ai_layer.sql` (`supabase db push`).
2. Habilitar extensiones para el cron (Dashboard → Database → Extensions): **pg_cron** y **pg_net**.

`SUPABASE_URL`, `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY` los inyecta
Supabase automáticamente en las Edge Functions — **no** hay que setearlos.

## 2. Secrets (clave del LLM y tarifas)

```bash
supabase secrets set LLM_API_KEY=sk-...            # obligatorio
supabase secrets set LLM_MODEL=claude-haiku-4-5-20251001   # opcional (default tier económico)
# Tarifas para el registro de costo (verificar precios vigentes del modelo):
supabase secrets set LLM_PRICE_IN=0.80            # USD por 1M tokens de entrada (ejemplo)
supabase secrets set LLM_PRICE_OUT=4.00           # USD por 1M tokens de salida (ejemplo)
```

> Si no fijas `LLM_PRICE_*`, el costo se registra como `0` (el tope mensual no
> morderá hasta que pongas tarifas reales). Confirma el precio/modelo vigente al implementar.

## 3. Desplegar

```bash
supabase functions deploy generate-briefing
```

## 4. Probar manualmente

```bash
curl -X POST 'https://<PROJECT_REF>.supabase.co/functions/v1/generate-briefing' \
  -H 'Authorization: Bearer <SERVICE_ROLE_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"force": true}'
```

Respuesta: `{ "date": "YYYY-MM-DD", "generated": [ { "user_id": "...", "status": "ok" } ] }`.
Luego abre el dashboard: el panel "Briefing del día" mostrará el texto de IA en vez del determinista.

Body opcional: `{ "user_id": "<uuid>" }` para un solo usuario, `{ "force": true }` para regenerar aunque ya exista.

## 5. Programar (~10:30 MX, antes de las 11:00)

México es UTC−6 (sin horario de verano) → 10:30 MX = **16:30 UTC**.

```sql
select cron.schedule(
  'prts-briefing-diario',
  '30 16 * * *',
  $$
    select net.http_post(
      url     := 'https://<PROJECT_REF>.supabase.co/functions/v1/generate-briefing',
      headers := jsonb_build_object(
                   'Authorization', 'Bearer <SERVICE_ROLE_KEY>',
                   'Content-Type',  'application/json'),
      body    := '{}'::jsonb
    );
  $$
);
```

> Mejor que pegar el `SERVICE_ROLE_KEY` en el job: guárdalo en **Supabase Vault** y léelo en el cron.
> Para cambiar el horario: `select cron.unschedule('prts-briefing-diario');` y vuelve a programar.

---

## Garantías de diseño

- **Degradación total:** si el LLM falla o no hay clave, se registra `error`/`degraded` en
  `ai_calls` y el dashboard usa `frasesBriefing()` determinista. Nada se rompe.
- **Costo controlado:** cada llamada registra tokens y costo; si el gasto del mes supera
  `ai_settings.monthly_cap_usd`, la generación se degrada sola.
- **Idempotente:** un briefing por `(user_id, brief_date)`; re-ejecutar no duplica (usa `force` para regenerar).
- **Prompts versionados:** `prompts/briefing.vN.ts`. Sube la versión al cambiar el texto y
  conserva la anterior; `ai_calls.prompt_version` registra cuál se usó.
