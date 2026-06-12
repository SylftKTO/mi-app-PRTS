// Edge Function: generate-briefing
// Pre-genera el briefing diario (≤5 líneas) y lo guarda en daily_briefings,
// para que el dashboard lo lea instantáneo sin llamar al LLM en cada apertura.
//
// Disparadores:
//   - Programado (~10:30 MX) vía pg_cron / cron de Supabase  -> sin body
//   - Manual (regenerar)                                     -> body { user_id?, force? }
//
// Principios: idempotente por (user_id, brief_date); respeta el tope mensual
// (ai_settings.monthly_cap_usd) degradando a 'degraded'; si el LLM falla,
// registra 'error' y NO rompe nada (el dashboard cae a frasesBriefing()).

import { createClient, type SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";
import { callLLM, costUsd, MODEL } from "../_shared/llm.ts";
import { SYSTEM, buildUser, VERSION } from "../_shared/prompts/briefing.v1.ts";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { ...CORS, "content-type": "application/json" } });

function hoyMX(): string {
  return new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
  const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!SUPABASE_URL || !SERVICE_KEY) return json({ error: "Faltan SUPABASE_URL / SERVICE_ROLE_KEY" }, 500);

  const sb = createClient(SUPABASE_URL, SERVICE_KEY);

  let body: { user_id?: string; force?: boolean } = {};
  try { body = await req.json(); } catch { /* sin body: corre para todos */ }

  const today = hoyMX();

  let q = sb.from("ai_settings").select("user_id, monthly_cap_usd, enabled").eq("enabled", true);
  if (body.user_id) q = q.eq("user_id", body.user_id);
  const { data: settings, error: sErr } = await q;
  if (sErr) return json({ error: sErr.message }, 500);

  const results = [];
  for (const s of settings ?? []) {
    results.push(await generarParaUsuario(sb, s, today, !!body.force));
  }
  return json({ date: today, generated: results });
});

async function generarParaUsuario(
  sb: SupabaseClient,
  s: { user_id: string; monthly_cap_usd: number | null },
  today: string,
  force: boolean,
) {
  const uid = s.user_id;

  // 1) Idempotencia
  if (!force) {
    const { data: existing } = await sb.from("daily_briefings")
      .select("id").eq("user_id", uid).eq("brief_date", today).maybeSingle();
    if (existing) return { user_id: uid, status: "skip", reason: "ya existe hoy" };
  }

  // 2) Tope mensual
  const monthStart = today.slice(0, 7) + "-01";
  const { data: spendRows } = await sb.from("ai_calls")
    .select("cost_usd").eq("user_id", uid).gte("created_at", monthStart);
  const spend = (spendRows ?? []).reduce((a, r) => a + Number(r.cost_usd), 0);
  if (s.monthly_cap_usd != null && spend >= Number(s.monthly_cap_usd)) {
    await logCall(sb, uid, "degraded", { error: "presupuesto mensual excedido" });
    return { user_id: uid, status: "degraded", reason: "tope mensual" };
  }

  // 3) Datos agregados (server-side, SECURITY DEFINER)
  const { data: brief, error: bErr } = await sb.rpc("dashboard_brief_for", { p_user: uid });
  if (bErr) return { user_id: uid, status: "error", reason: bErr.message };

  // 4) LLM + persistencia (con degradación)
  const t0 = Date.now();
  try {
    const out = await callLLM({ system: SYSTEM, user: buildUser(brief), maxTokens: 300 });
    const latency = Date.now() - t0;

    const { error: upErr } = await sb.from("daily_briefings").upsert({
      user_id: uid, brief_date: today, text: out.text,
      model: out.model, prompt_version: VERSION, source: brief,
    }, { onConflict: "user_id,brief_date" });
    if (upErr) throw new Error(upErr.message);

    await logCall(sb, uid, "ok", {
      model: out.model, inT: out.inputTokens, outT: out.outputTokens,
      cost: costUsd(out.inputTokens, out.outputTokens), latency,
    });
    return { user_id: uid, status: "ok" };
  } catch (err) {
    await logCall(sb, uid, "error", { latency: Date.now() - t0, error: String(err) });
    return { user_id: uid, status: "error", reason: String(err) };
  }
}

async function logCall(
  sb: SupabaseClient,
  uid: string,
  status: "ok" | "error" | "degraded",
  extra: { model?: string; inT?: number; outT?: number; cost?: number; latency?: number; error?: string } = {},
) {
  await sb.from("ai_calls").insert({
    user_id: uid,
    agent: "briefing",
    prompt_version: VERSION,
    model: extra.model ?? MODEL,
    input_tokens: extra.inT ?? 0,
    output_tokens: extra.outT ?? 0,
    cost_usd: extra.cost ?? 0,
    latency_ms: extra.latency ?? null,
    status,
    error: extra.error ?? null,
    ref_table: status === "ok" ? "daily_briefings" : null,
  });
}
