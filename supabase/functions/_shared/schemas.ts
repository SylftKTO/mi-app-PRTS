// Validación de las salidas del LLM (vocabularios cerrados, sin dependencias).
// Si el JSON del modelo no valida → el llamador reintenta una vez y luego degrada.

export interface InboxSuggestion {
  module: "tareas" | "dieta" | "apuntes" | "proyectos" | "recordatorio" | "gym" | "semana" | "desconocido";
  action: "create" | "none";
  payload: Record<string, unknown>;
  confidence: number;
  summary: string;
}

export interface CommandIntent {
  intent: "open" | "navigate" | "summary" | "create_task" | "log_weight" | "weather" | "unknown";
  params: Record<string, unknown>;
  speak: string;
  confidence: number;
}

const INBOX_MODULES = ["tareas", "dieta", "apuntes", "proyectos", "recordatorio", "gym", "semana", "desconocido"];
const INTENTS = ["open", "navigate", "summary", "create_task", "log_weight", "weather", "unknown"];
const ORIGINS = ["escuela", "wolves", "levelup", "personal"];
const PRIORITIES = ["alta", "media", "baja"];
const MEALS = ["desayuno", "comida", "pregym", "cena", "snack"];
const VIEWS = ["dashboard", "tareas", "semana", "proyectos", "gym", "dieta", "apuntes"];

const isStr = (v: unknown): v is string => typeof v === "string";
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const isDateOrNull = (v: unknown) => v === null || v === undefined || (isStr(v) && /^\d{4}-\d{2}-\d{2}$/.test(v));
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === "object" && !Array.isArray(v);

/** Extrae el primer objeto JSON del texto del modelo (tolera fences de markdown). */
export function parseJSON(text: string): unknown | null {
  const m = text.match(/\{[\s\S]*\}/);
  if (!m) return null;
  try { return JSON.parse(m[0]); } catch { return null; }
}

export function validateInbox(raw: unknown): InboxSuggestion | null {
  if (!isObj(raw)) return null;
  const { module, action, payload, confidence, summary } = raw as Record<string, unknown>;
  if (!isStr(module) || !INBOX_MODULES.includes(module)) return null;
  if (action !== "create" && action !== "none") return null;
  if (!isNum(confidence) || confidence < 0 || confidence > 1) return null;
  if (!isStr(summary) || !summary.trim()) return null;
  const p = isObj(payload) ? payload : {};

  if (action === "create") {
    switch (module) {
      case "tareas":
        if (!isStr(p.title) || !p.title.trim()) return null;
        if (!isStr(p.origin) || !ORIGINS.includes(p.origin)) p.origin = "personal";
        if (!isStr(p.priority) || !PRIORITIES.includes(p.priority)) p.priority = "media";
        if (!isDateOrNull(p.deadline)) p.deadline = null;
        break;
      case "recordatorio":
        if (!isStr(p.title) || !p.title.trim()) return null;
        if (!isDateOrNull(p.deadline)) p.deadline = null;
        break;
      case "dieta":
        if (!isStr(p.name) || !p.name.trim()) return null;
        if (!isStr(p.meal) || !MEALS.includes(p.meal)) return null;
        for (const k of ["kcal", "protein_g", "carbs_g", "fat_g"]) if (!isNum(p[k]) || (p[k] as number) < 0) p[k] = 0;
        break;
      case "apuntes":
        if (!isStr(p.subject) && !isStr(p.topic)) return null;
        for (const k of ["subject", "topic", "summary"]) if (!isStr(p[k])) p[k] = "";
        break;
      case "proyectos":
        if (!isStr(p.name) || !p.name.trim()) return null;
        if (!isDateOrNull(p.due_date)) p.due_date = null;
        break;
      default:
        return null; // gym/semana/desconocido no aceptan "create"
    }
  }
  return { module, action, payload: p, confidence, summary } as InboxSuggestion;
}

export interface InsightItem {
  kind: "gym" | "peso" | "dieta" | "tareas" | "general";
  title: string;
  detail: string;
}

const INSIGHT_KINDS = ["gym", "peso", "dieta", "tareas", "general"];

export function validateInsights(raw: unknown): InsightItem[] | null {
  if (!isObj(raw) || !Array.isArray((raw as Record<string, unknown>).items)) return null;
  const items = (raw as { items: unknown[] }).items;
  if (items.length < 1 || items.length > 6) return null;
  const out: InsightItem[] = [];
  for (const it of items) {
    if (!isObj(it)) return null;
    const kind = isStr(it.kind) && INSIGHT_KINDS.includes(it.kind) ? it.kind : "general";
    if (!isStr(it.title) || !it.title.trim() || !isStr(it.detail) || !it.detail.trim()) return null;
    out.push({ kind, title: it.title.trim(), detail: it.detail.trim() } as InsightItem);
  }
  return out;
}

export function validateCommand(raw: unknown): CommandIntent | null {
  if (!isObj(raw)) return null;
  const { intent, params, speak, confidence } = raw as Record<string, unknown>;
  if (!isStr(intent) || !INTENTS.includes(intent)) return null;
  if (!isNum(confidence) || confidence < 0 || confidence > 1) return null;
  const p = isObj(params) ? params : {};
  const sp = isStr(speak) ? speak : "";

  switch (intent) {
    case "open":
      if (p.target !== "spotify") return null;
      if (!isStr(p.deep_link) ||
          !(p.deep_link.startsWith("spotify:") || p.deep_link.startsWith("https://open.spotify.com/"))) return null;
      break;
    case "weather":
      if (p.location !== null && p.location !== undefined && !isStr(p.location)) p.location = null;
      break;
    case "navigate":
      if (!isStr(p.view) || !VIEWS.includes(p.view)) return null;
      break;
    case "summary":
      if (!isStr(p.scope) || !["dia", "tareas", "gym"].includes(p.scope)) p.scope = "dia";
      break;
    case "create_task":
      if (!isStr(p.title) || !p.title.trim()) return null;
      if (!isStr(p.origin) || !ORIGINS.includes(p.origin)) p.origin = "personal";
      if (!isStr(p.priority) || !PRIORITIES.includes(p.priority)) p.priority = "media";
      if (!isDateOrNull(p.deadline)) p.deadline = null;
      break;
    case "log_weight":
      if (!isNum(p.weight_kg) || p.weight_kg <= 0 || p.weight_kg > 400) return null;
      if (!isDateOrNull(p.date)) p.date = null;
      break;
  }
  return { intent, params: p, speak: sp, confidence } as CommandIntent;
}
