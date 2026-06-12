// Edge Function: interpret-command (Fase 4.2)
// Interpreta un comando freeform (voz/texto) y devuelve UNA intención del
// vocabulario cerrado. NUNCA ejecuta efectos: el cliente la ejecuta contra
// su whitelist (app/ai/actions.js).
//
// Las intenciones simples (navegar, resumir) se resuelven en el cliente SIN
// llamar aquí (router local); solo lo freeform llega a esta función.
//
//   POST { text, context? }  -> { status, intent? }
//
// Seguridad: JWT del usuario (RLS). Degradación: ante error el cliente
// muestra la transcripción como captura normal — no se pierde nada.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { callLLM, costUsd, MODEL } from "../_shared/llm.ts";
import { parseJSON, validateCommand, type CommandIntent } from "../_shared/schemas.ts";
import { SYSTEM, buildUser, VERSION } from "../_shared/prompts/command.v4.ts";

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

  let body: { text?: string; context?: unknown } = {};
  try { body = await req.json(); } catch { /* sin body */ }
  const text = (body.text ?? "").trim();
  if (!text) return json({ error: "Falta text" }, 400);
  if (text.length > 500) return json({ error: "Comando demasiado largo" }, 400);

  // Tope mensual -> degradación (el cliente vuelca el texto a captura)
  const { data: spend } = await sb.rpc("ai_spend_month");
  const { data: cfg } = await sb.from("ai_settings").select("monthly_cap_usd, enabled").maybeSingle();
  if (cfg && (!cfg.enabled || (cfg.monthly_cap_usd != null && Number(spend ?? 0) >= Number(cfg.monthly_cap_usd)))) {
    return json({ status: "degraded", reason: "IA deshabilitada o tope mensual excedido" });
  }

  const t0 = Date.now();
  try {
    let intent: CommandIntent | null = null;
    let out;
    for (let i = 0; i < 2 && !intent; i++) {
      out = await callLLM({ system: SYSTEM, user: buildUser(text, hoyMX(), body.context), maxTokens: 300 });
      intent = validateCommand(parseJSON(out.text));
    }
    if (!intent || !out) throw new Error("salida del modelo no valida el schema");

    await logCall(sb, user.id, "ok", {
      model: out.model, inT: out.inputTokens, outT: out.outputTokens,
      cost: costUsd(out.inputTokens, out.outputTokens), latency: Date.now() - t0,
    });
    return json({ status: "ok", intent });
  } catch (err) {
    await logCall(sb, user.id, "error", { latency: Date.now() - t0, error: String(err) });
    return json({ status: "error", reason: String(err) });
  }
});

async function logCall(
  sb: ReturnType<typeof createClient>,
  uid: string,
  status: "ok" | "error",
  extra: { model?: string; inT?: number; outT?: number; cost?: number; latency?: number; error?: string } = {},
) {
  await sb.from("ai_calls").insert({
    user_id: uid,
    agent: "command",
    prompt_version: VERSION,
    model: extra.model ?? MODEL,
    input_tokens: extra.inT ?? 0,
    output_tokens: extra.outT ?? 0,
    cost_usd: extra.cost ?? 0,
    latency_ms: extra.latency ?? null,
    status,
    error: extra.error ?? null,
  });
}
