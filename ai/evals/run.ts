// Runner de regresión de prompts (§10.7). Corre los casos contra el LLM y
// compara con lo esperado. Úsalo ANTES de subir un prompt.vN+1:
//
//   $env:LLM_API_KEY = "sk-..."          # PowerShell
//   deno run --allow-net --allow-env --allow-read ai/evals/run.ts inbox
//   deno run --allow-net --allow-env --allow-read ai/evals/run.ts command
//
// Compara aciertos entre versiones cambiando el import del prompt abajo.

import { callLLM } from "../../supabase/functions/_shared/llm.ts";
import { parseJSON, validateCommand, validateInbox } from "../../supabase/functions/_shared/schemas.ts";
import * as inboxPrompt from "../../supabase/functions/_shared/prompts/inbox.v1.ts";
import * as commandPrompt from "../../supabase/functions/_shared/prompts/command.v2.ts";

const agente = Deno.args[0];
if (agente !== "inbox" && agente !== "command") {
  console.error("Uso: deno run --allow-net --allow-env --allow-read ai/evals/run.ts <inbox|command>");
  Deno.exit(1);
}

const hoy = new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });
const casos = (await Deno.readTextFile(new URL(`./${agente}.cases.jsonl`, import.meta.url)))
  .trim().split("\n").map((l) => JSON.parse(l));

// Coincidencia parcial: todo lo declarado en `expect` debe estar en la salida
function matches(expect: unknown, actual: unknown): boolean {
  if (expect === null || typeof expect !== "object") return expect === actual;
  if (actual === null || typeof actual !== "object") return false;
  return Object.entries(expect as Record<string, unknown>)
    .every(([k, v]) => matches(v, (actual as Record<string, unknown>)[k]));
}

let ok = 0;
for (const caso of casos) {
  const entrada = agente === "inbox" ? caso.raw_text : caso.text;
  const prompt = agente === "inbox" ? inboxPrompt : commandPrompt;
  const out = await callLLM({ system: prompt.SYSTEM, user: prompt.buildUser(entrada, hoy), maxTokens: 350 });
  const parsed = agente === "inbox" ? validateInbox(parseJSON(out.text)) : validateCommand(parseJSON(out.text));
  const pass = parsed !== null && matches(caso.expect, parsed);
  if (pass) ok++;
  console.log(`${pass ? "✓" : "✗"} "${entrada}"` +
    (pass ? "" : `\n    esperado ⊇ ${JSON.stringify(caso.expect)}\n    obtenido   ${JSON.stringify(parsed)}`));
}
console.log(`\n${prompVersion()} — ${ok}/${casos.length} aciertos (${Math.round((ok / casos.length) * 100)}%)`);

function prompVersion() {
  return agente === "inbox" ? inboxPrompt.VERSION : commandPrompt.VERSION;
}
