// Edge Function: generate-insights (Fase 4.4)
// Analiza ~4 semanas de datos (gym, peso, dieta, tareas) y guarda una lista
// corta de hallazgos accionables en ai_insights. El dashboard lee la última.
//
// Disparador: botón "Analizar" en el dashboard (y opcionalmente cron semanal).
//   POST { force? }  -> regenera aunque ya exista para el periodo
//
// Contexto mínimo: los agregados se calculan AQUÍ y se manda un JSON compacto,
// nunca tablas completas. Seguridad: JWT del usuario (RLS). Degradación: ante
// error se responde 'error' y el panel muestra su estado manual.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { callLLM, costUsd, MODEL } from "../_shared/llm.ts";
import { parseJSON, validateInsights } from "../_shared/schemas.ts";
import { SYSTEM, buildUser, VERSION } from "../_shared/prompts/insights.v1.ts";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { ...CORS, "content-type": "application/json" } });

const DIAS_VENTANA = 28;
const hoyMX = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });
const restarDias = (iso: string, n: number) => {
  const d = new Date(iso + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
  const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY");
  if (!SUPABASE_URL || !ANON_KEY) return json({ error: "Faltan SUPABASE_URL / ANON_KEY" }, 500);

  const auth = req.headers.get("Authorization") ?? "";
  const sb = createClient(SUPABASE_URL, ANON_KEY, { global: { headers: { Authorization: auth } } });
  const { data: { user }, error: uErr } = await sb.auth.getUser();
  if (uErr || !user) return json({ error: "No autenticado" }, 401);

  let body: { force?: boolean } = {};
  try { body = await req.json(); } catch { /* sin body */ }

  const hoy = hoyMX();
  const desde = restarDias(hoy, DIAS_VENTANA);

  // Idempotencia por periodo (un análisis por día de corte)
  if (!body.force) {
    const { data: existing } = await sb.from("ai_insights")
      .select("id, items, period_start, period_end").eq("period_end", hoy).maybeSingle();
    if (existing) return json({ status: "ok", cached: true, insight: existing });
  }

  // Tope mensual -> degradación
  const { data: spend } = await sb.rpc("ai_spend_month");
  const { data: cfg } = await sb.from("ai_settings").select("monthly_cap_usd, enabled").maybeSingle();
  if (cfg && (!cfg.enabled || (cfg.monthly_cap_usd != null && Number(spend ?? 0) >= Number(cfg.monthly_cap_usd)))) {
    return json({ status: "degraded", reason: "IA deshabilitada o tope mensual excedido" });
  }

  // --- Agregados (RLS filtra por usuario; ventana de 4 semanas) ---
  const source = await agregar(sb, desde, hoy);
  if (!source.suficiente) {
    return json({ status: "insufficient", reason: "Aún hay pocos datos para detectar patrones (se requieren ~2+ semanas de uso)." });
  }

  const t0 = Date.now();
  try {
    let items = null;
    let out;
    for (let i = 0; i < 2 && !items; i++) {
      out = await callLLM({ system: SYSTEM, user: buildUser(source), maxTokens: 600 });
      items = validateInsights(parseJSON(out.text));
    }
    if (!items || !out) throw new Error("salida del modelo no valida el schema");

    const { data: row, error: upErr } = await sb.from("ai_insights").upsert({
      user_id: user.id, period_start: desde, period_end: hoy,
      items, model: out.model, prompt_version: VERSION, source,
    }, { onConflict: "user_id,period_end" }).select("id, items, period_start, period_end").single();
    if (upErr) throw new Error(upErr.message);

    await logCall(sb, user.id, "ok", row.id, {
      model: out.model, inT: out.inputTokens, outT: out.outputTokens,
      cost: costUsd(out.inputTokens, out.outputTokens), latency: Date.now() - t0,
    });
    return json({ status: "ok", insight: row });
  } catch (err) {
    await logCall(sb, user.id, "error", null, { latency: Date.now() - t0, error: String(err) });
    return json({ status: "error", reason: String(err) });
  }
});

// Agregados compactos: lo justo para detectar patrones, nunca tablas completas.
async function agregar(sb: ReturnType<typeof createClient>, desde: string, hasta: string) {
  // Gym: sesiones por semana + progresión por ejercicio (máximo 1.ª vs 2.ª mitad)
  const { data: sesiones } = await sb.from("workout_sessions")
    .select("id, session_date").gte("session_date", desde).lte("session_date", hasta);
  const ids = (sesiones ?? []).map((s: { id: string }) => s.id);
  let progresion: unknown[] = [];
  if (ids.length) {
    const { data: sets } = await sb.from("workout_sets")
      .select("exercise_id, weight_kg, reps, created_at, exercises(name)")
      .in("session_id", ids).limit(2000);
    const mitad = restarDias(hasta, Math.floor(DIAS_VENTANA / 2));
    const porEj = new Map<string, { name: string; maxIni: number; maxFin: number; sets: number }>();
    for (const s of (sets ?? []) as Array<{ exercise_id: string; weight_kg: number; created_at: string; exercises: { name: string } | null }>) {
      const e = porEj.get(s.exercise_id) ?? { name: s.exercises?.name ?? "?", maxIni: 0, maxFin: 0, sets: 0 };
      e.sets++;
      if (s.created_at.slice(0, 10) < mitad) e.maxIni = Math.max(e.maxIni, Number(s.weight_kg));
      else e.maxFin = Math.max(e.maxFin, Number(s.weight_kg));
      porEj.set(s.exercise_id, e);
    }
    progresion = [...porEj.values()].filter((e) => e.sets >= 4)
      .map((e) => ({ ejercicio: e.name, max_kg_inicio: e.maxIni || null, max_kg_fin: e.maxFin || null, sets: e.sets }));
  }

  // Peso corporal
  const { data: pesos } = await sb.from("body_weights")
    .select("measured_on, weight_kg").gte("measured_on", desde).order("measured_on");

  // Dieta: kcal y proteína por día (promedios)
  const { data: comidas } = await sb.from("meal_logs")
    .select("log_date, kcal, protein_g").gte("log_date", desde).limit(2000);
  const porDia = new Map<string, { kcal: number; prot: number }>();
  for (const c of (comidas ?? []) as Array<{ log_date: string; kcal: number; protein_g: number }>) {
    const d = porDia.get(c.log_date) ?? { kcal: 0, prot: 0 };
    d.kcal += Number(c.kcal); d.prot += Number(c.protein_g);
    porDia.set(c.log_date, d);
  }
  const dias = [...porDia.values()];
  const prom = (f: (d: { kcal: number; prot: number }) => number) =>
    dias.length ? Math.round(dias.reduce((a, d) => a + f(d), 0) / dias.length) : null;

  // Tareas: completadas vs pendientes por origen
  const { data: tareas } = await sb.from("tasks")
    .select("origin, status, deadline, completed_at").gte("created_at", desde + "T00:00:00Z").limit(1000);
  const porOrigen: Record<string, { completadas: number; pendientes: number; vencidas: number }> = {};
  for (const t of (tareas ?? []) as Array<{ origin: string; status: string; deadline: string | null }>) {
    const o = (porOrigen[t.origin] ??= { completadas: 0, pendientes: 0, vencidas: 0 });
    if (t.status === "completada") o.completadas++;
    else if (t.status === "pendiente") { o.pendientes++; if (t.deadline && t.deadline < hasta) o.vencidas++; }
  }

  const nSesiones = (sesiones ?? []).length;
  return {
    periodo: { desde, hasta, dias: DIAS_VENTANA },
    gym: { sesiones: nSesiones, sesiones_por_semana: Math.round((nSesiones / DIAS_VENTANA) * 7 * 10) / 10, progresion },
    peso_corporal: (pesos ?? []).map((p: { measured_on: string; weight_kg: number }) => ({ fecha: p.measured_on, kg: Number(p.weight_kg) })),
    dieta: { dias_registrados: dias.length, kcal_promedio: prom((d) => d.kcal), proteina_promedio_g: prom((d) => d.prot) },
    tareas: porOrigen,
    // Suficiencia mínima: algo de gym O dieta O tareas que analizar
    suficiente: nSesiones >= 4 || dias.length >= 7 || (tareas ?? []).length >= 10,
  };
}

async function logCall(
  sb: ReturnType<typeof createClient>,
  uid: string,
  status: "ok" | "error",
  refId: string | null,
  extra: { model?: string; inT?: number; outT?: number; cost?: number; latency?: number; error?: string } = {},
) {
  await sb.from("ai_calls").insert({
    user_id: uid,
    agent: "insights",
    prompt_version: VERSION,
    model: extra.model ?? MODEL,
    input_tokens: extra.inT ?? 0,
    output_tokens: extra.outT ?? 0,
    cost_usd: extra.cost ?? 0,
    latency_ms: extra.latency ?? null,
    status,
    error: extra.error ?? null,
    ref_table: refId ? "ai_insights" : null,
    ref_id: refId,
  });
}
