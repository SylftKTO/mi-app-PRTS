// Edge Function: process-inbox (Fase 4.1)
// Clasifica capturas pendientes de inbox_entries y devuelve SUGERENCIAS.
// NUNCA escribe en los módulos: el cliente muestra la tarjeta
// "PRTS interpretó esto como… [Confirmar] [Editar] [Descartar]" y, al
// confirmar, inserta él mismo (RLS) y marca la entrada como procesada.
//
// Disparador: botón "Procesar" en el dashboard.
//   POST { entry_id? }  -> procesa esa entrada, o las pendientes (máx. 5)
//
// Seguridad: actúa con el JWT del usuario (RLS protege todas las lecturas
// y el log de ai_calls). Sin service role.
//
// Degradación: presupuesto excedido -> 'degraded'; LLM/JSON inválido tras
// 1 reintento -> 'error'; la entrada queda 'pendiente' (flujo manual de hoy).

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { callLLM, costUsd, MODEL } from "../_shared/llm.ts";
import { parseJSON, validateInbox, type InboxSuggestion } from "../_shared/schemas.ts";
import { SYSTEM, buildUser, VERSION } from "../_shared/prompts/inbox.v1.ts";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { ...CORS, "content-type": "application/json" } });

const hoyMX = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
  const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY");
  if (!SUPABASE_URL || !ANON_KEY) return json({ error: "Faltan SUPABASE_URL / ANON_KEY" }, 500);

  const auth = req.headers.get("Authorization") ?? "";
  const sb = createClient(SUPABASE_URL, ANON_KEY, { global: { headers: { Authorization: auth } } });
  const { data: { user }, error: uErr } = await sb.auth.getUser();
  if (uErr || !user) return json({ error: "No autenticado" }, 401);

  let body: { entry_id?: string } = {};
  try { body = await req.json(); } catch { /* sin body: pendientes */ }

  // Tope mensual -> degradación (el usuario sigue procesando a mano)
  const { data: spend } = await sb.rpc("ai_spend_month");
  const { data: cfg } = await sb.from("ai_settings").select("monthly_cap_usd, enabled").maybeSingle();
  if (cfg && (!cfg.enabled || (cfg.monthly_cap_usd != null && Number(spend ?? 0) >= Number(cfg.monthly_cap_usd)))) {
    return json({ status: "degraded", reason: "IA deshabilitada o tope mensual excedido", suggestions: [] });
  }

  let q = sb.from("inbox_entries").select("id, raw_text").eq("status", "pendiente")
    .order("created_at", { ascending: false }).limit(5);
  // Sin entry_id (auto/cron) sólo procesa las aún SIN sugerencia cacheada
  // (result null) → idempotente y sin re-gastar LLM al reabrir el dashboard.
  if (body.entry_id) q = q.eq("id", body.entry_id);
  else q = q.is("result", null);
  const { data: entries, error: eErr } = await q;
  if (eErr) return json({ error: eErr.message }, 500);
  if (!entries?.length) return json({ status: "ok", suggestions: [] });

  const today = hoyMX();
  const suggestions = [];
  for (const e of entries) {
    suggestions.push(await clasificar(sb, user.id, e, today));
  }
  return json({ status: "ok", suggestions });
});

async function clasificar(
  sb: ReturnType<typeof createClient>,
  uid: string,
  entry: { id: string; raw_text: string },
  today: string,
) {
  const t0 = Date.now();
  try {
    let suggestion: InboxSuggestion | null = null;
    let out;
    // 1 reintento si el JSON no valida; luego degradación
    for (let i = 0; i < 2 && !suggestion; i++) {
      out = await callLLM({ system: SYSTEM, user: buildUser(entry.raw_text, today), maxTokens: 350 });
      suggestion = validateInbox(parseJSON(out.text));
    }
    if (!suggestion || !out) throw new Error("salida del modelo no valida el schema");

    // Cachear la sugerencia en la entrada (sigue 'pendiente'): el dashboard la
    // muestra al abrir sin re-llamar al LLM. Se sobrescribe al confirmar/descartar.
    await sb.from("inbox_entries").update({ result: { cached_suggestion: suggestion } }).eq("id", entry.id);

    await logCall(sb, uid, "ok", entry.id, {
      model: out.model, inT: out.inputTokens, outT: out.outputTokens,
      cost: costUsd(out.inputTokens, out.outputTokens), latency: Date.now() - t0,
    });
    return { id: entry.id, raw_text: entry.raw_text, status: "ok", suggestion };
  } catch (err) {
    await logCall(sb, uid, "error", entry.id, { latency: Date.now() - t0, error: String(err) });
    return { id: entry.id, raw_text: entry.raw_text, status: "error", suggestion: null };
  }
}

async function logCall(
  sb: ReturnType<typeof createClient>,
  uid: string,
  status: "ok" | "error",
  refId: string,
  extra: { model?: string; inT?: number; outT?: number; cost?: number; latency?: number; error?: string } = {},
) {
  await sb.from("ai_calls").insert({
    user_id: uid,
    agent: "inbox",
    prompt_version: VERSION,
    model: extra.model ?? MODEL,
    input_tokens: extra.inT ?? 0,
    output_tokens: extra.outT ?? 0,
    cost_usd: extra.cost ?? 0,
    latency_ms: extra.latency ?? null,
    status,
    error: extra.error ?? null,
    ref_table: "inbox_entries",
    ref_id: refId,
  });
}
