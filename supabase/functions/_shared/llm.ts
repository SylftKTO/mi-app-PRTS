// Cliente LLM aislado del proveedor (Anthropic por defecto).
// Cambiar de proveedor = tocar SOLO este archivo. El resto del sistema
// consume callLLM() y costUsd() sin saber quién está detrás.
//
// Variables de entorno (supabase secrets set ...):
//   LLM_API_KEY     -> clave del proveedor (obligatoria)
//   LLM_MODEL       -> id del modelo (default: tier económico)
//   LLM_PRICE_IN    -> USD por 1M tokens de entrada  (verificar vigente)
//   LLM_PRICE_OUT   -> USD por 1M tokens de salida   (verificar vigente)

export interface LLMResult {
  text: string;
  inputTokens: number;
  outputTokens: number;
  model: string;
}

const API_URL = "https://api.anthropic.com/v1/messages";
export const MODEL = Deno.env.get("LLM_MODEL") ?? "claude-haiku-4-5-20251001";

// Leídos en tiempo de llamada (no en módulo load) para permitir
// que los tests sobreescriban el entorno sin pelea de hoisting.
function apiKey() { return Deno.env.get("LLM_API_KEY") ?? ""; }
function priceIn() { return Number(Deno.env.get("LLM_PRICE_IN") ?? "0"); }
function priceOut() { return Number(Deno.env.get("LLM_PRICE_OUT") ?? "0"); }

export function costUsd(inTok: number, outTok: number): number {
  return (inTok / 1e6) * priceIn() + (outTok / 1e6) * priceOut();
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// --- Circuit breaker (§10.5): N fallos consecutivos → pausa temporal ---
// Estado en memoria del isolate (se reinicia en cold start, suficiente para
// evitar martillar al proveedor durante una caída). Mientras está abierto,
// callLLM lanza de inmediato y el llamador degrada a manual.
const BREAKER_MAX_FAILS = 3;
const BREAKER_PAUSE_MS = 5 * 60 * 1000;
let consecutiveFails = 0;
let breakerOpenUntil = 0;

/**
 * Llama al LLM con reintentos + backoff exponencial en 429/5xx y circuit
 * breaker ante fallos consecutivos. Lanza si agota reintentos, ante un 4xx
 * no reintentable o con el breaker abierto. El llamador decide la
 * degradación (registrar 'error' y seguir manual).
 */
export async function callLLM(opts: {
  system: string;
  user: string;
  maxTokens?: number;
}): Promise<LLMResult> {
  const API_KEY = apiKey();
  if (!API_KEY) throw new Error("LLM_API_KEY no configurada");
  if (Date.now() < breakerOpenUntil) {
    throw new Error("circuit breaker abierto: IA en pausa temporal tras fallos repetidos");
  }

  const body = {
    model: MODEL,
    max_tokens: opts.maxTokens ?? 400,
    system: opts.system,
    messages: [{ role: "user", content: opts.user }],
  };

  const backoff = [500, 1500, 4000];
  let lastErr: unknown;

  for (let attempt = 0; attempt <= backoff.length; attempt++) {
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": API_KEY,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify(body),
      });

      if (res.status === 429 || res.status >= 500) {
        throw new Error(`LLM ${res.status}: ${await res.text()}`);
      }
      if (!res.ok) {
        // 4xx no reintentable
        throw Object.assign(new Error(`LLM ${res.status}: ${await res.text()}`), { fatal: true });
      }

      const data = await res.json();
      const text = (data.content ?? [])
        .filter((c: { type: string }) => c.type === "text")
        .map((c: { text: string }) => c.text)
        .join("")
        .trim();

      consecutiveFails = 0;
      return {
        text,
        inputTokens: data.usage?.input_tokens ?? 0,
        outputTokens: data.usage?.output_tokens ?? 0,
        model: data.model ?? MODEL,
      };
    } catch (err) {
      lastErr = err;
      if ((err as { fatal?: boolean })?.fatal) break;
      if (attempt < backoff.length) await sleep(backoff[attempt]);
    }
  }
  if (++consecutiveFails >= BREAKER_MAX_FAILS) {
    breakerOpenUntil = Date.now() + BREAKER_PAUSE_MS;
    consecutiveFails = 0;
  }
  throw lastErr instanceof Error ? lastErr : new Error("LLM falló tras reintentos");
}

/** Solo para tests — reinicia el estado del circuit breaker. */
export function _resetBreakerForTest() {
  consecutiveFails = 0;
  breakerOpenUntil = 0;
}
