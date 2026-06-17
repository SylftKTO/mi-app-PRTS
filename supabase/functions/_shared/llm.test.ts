// Tests unitarios para llm.ts — correr con:
//   LLM_API_KEY=sk-test LLM_PRICE_IN=1.0 LLM_PRICE_OUT=5.0 \
//   deno test --allow-env supabase/functions/_shared/llm.test.ts
//
// fetch queda interceptado por stub; ninguna llamada real sale a la red.
import { assertEquals, assertRejects, assertMatch } from "jsr:@std/assert";
import { stub } from "jsr:@std/testing/mock";
import { callLLM, costUsd, _resetBreakerForTest } from "./llm.ts";

// ─── costUsd ─────────────────────────────────────────────────────────────────

Deno.test("costUsd: cálculo básico con precios de entorno", () => {
  Deno.env.set("LLM_PRICE_IN", "1.0");
  Deno.env.set("LLM_PRICE_OUT", "5.0");
  // 1M tokens in @ $1/M = $1.00, 1M tokens out @ $5/M = $5.00 → $6.00
  assertEquals(costUsd(1_000_000, 1_000_000), 6.0);
});

Deno.test("costUsd: tokens parciales", () => {
  Deno.env.set("LLM_PRICE_IN", "1.0");
  Deno.env.set("LLM_PRICE_OUT", "5.0");
  // 500 in @ $1/M = $0.0005, 200 out @ $5/M = $0.001 → $0.0015
  const result = costUsd(500, 200);
  assertEquals(Math.round(result * 1e7) / 1e7, 0.0015);
});

Deno.test("costUsd: precios en cero → costo cero", () => {
  Deno.env.set("LLM_PRICE_IN", "0");
  Deno.env.set("LLM_PRICE_OUT", "0");
  assertEquals(costUsd(100_000, 50_000), 0);
});

Deno.test("costUsd: tokens cero → costo cero", () => {
  Deno.env.set("LLM_PRICE_IN", "1.0");
  Deno.env.set("LLM_PRICE_OUT", "5.0");
  assertEquals(costUsd(0, 0), 0);
});

// ─── callLLM — happy path ────────────────────────────────────────────────────

function makeOkResponse(text: string, inputTokens = 10, outputTokens = 5) {
  return new Response(JSON.stringify({
    content: [{ type: "text", text }],
    usage: { input_tokens: inputTokens, output_tokens: outputTokens },
    model: "claude-haiku-4-5-20251001",
  }), { status: 200 });
}

Deno.test("callLLM: devuelve texto y tokens en happy path", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  using _f = stub(globalThis, "fetch", async () => makeOkResponse("hola mundo", 20, 3));
  const r = await callLLM({ system: "sys", user: "user" });
  assertEquals(r.text, "hola mundo");
  assertEquals(r.inputTokens, 20);
  assertEquals(r.outputTokens, 3);
  assertEquals(r.model, "claude-haiku-4-5-20251001");
});

Deno.test("callLLM: trimmea el texto de la respuesta", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  using _f = stub(globalThis, "fetch", async () => makeOkResponse("  respuesta con espacios  "));
  const r = await callLLM({ system: "s", user: "u" });
  assertEquals(r.text, "respuesta con espacios");
});

Deno.test("callLLM: concatena bloques de texto múltiples", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  using _f = stub(globalThis, "fetch", async () => new Response(JSON.stringify({
    content: [
      { type: "text", text: "parte uno" },
      { type: "tool_use", id: "t1" },      // ignorado
      { type: "text", text: " parte dos" },
    ],
    usage: { input_tokens: 5, output_tokens: 5 },
    model: "claude-haiku-4-5-20251001",
  }), { status: 200 }));
  const r = await callLLM({ system: "s", user: "u" });
  assertEquals(r.text, "parte uno parte dos");
});

Deno.test("callLLM: usa usage.input_tokens = 0 si falta usage", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  using _f = stub(globalThis, "fetch", async () => new Response(JSON.stringify({
    content: [{ type: "text", text: "ok" }],
    model: "claude-haiku-4-5-20251001",
    // sin usage
  }), { status: 200 }));
  const r = await callLLM({ system: "s", user: "u" });
  assertEquals(r.inputTokens, 0);
  assertEquals(r.outputTokens, 0);
});

// ─── callLLM — sin API key ───────────────────────────────────────────────────

Deno.test("callLLM: lanza error si LLM_API_KEY está vacía", async () => {
  Deno.env.set("LLM_API_KEY", "");
  _resetBreakerForTest();
  await assertRejects(
    () => callLLM({ system: "s", user: "u" }),
    Error,
    "LLM_API_KEY no configurada",
  );
});

// ─── callLLM — reintentos ─────────────────────────────────────────────────────

Deno.test("callLLM: reintenta tras 429 y devuelve resultado al recuperarse", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  let intentos = 0;
  using _f = stub(globalThis, "fetch", async () => {
    intentos++;
    if (intentos < 3) return new Response("rate limited", { status: 429 });
    return makeOkResponse("ok tras reintento");
  });
  const r = await callLLM({ system: "s", user: "u" });
  assertEquals(r.text, "ok tras reintento");
  assertEquals(intentos, 3);
});

Deno.test("callLLM: reintenta tras 500 y devuelve resultado al recuperarse", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  let intentos = 0;
  using _f = stub(globalThis, "fetch", async () => {
    intentos++;
    if (intentos === 1) return new Response("server error", { status: 500 });
    return makeOkResponse("ok");
  });
  const r = await callLLM({ system: "s", user: "u" });
  assertEquals(r.text, "ok");
});

Deno.test("callLLM: 4xx (no reintentable) falla de inmediato", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();
  let intentos = 0;
  using _f = stub(globalThis, "fetch", async () => {
    intentos++;
    return new Response("unauthorized", { status: 401 });
  });
  await assertRejects(() => callLLM({ system: "s", user: "u" }), Error, "LLM 401");
  assertEquals(intentos, 1);  // sin reintento
});

// ─── callLLM — circuit breaker ───────────────────────────────────────────────
// Este grupo de tests modifica el estado global del módulo.
// Se ejecuta al final para no afectar los tests anteriores.

Deno.test("callLLM: circuit breaker se abre tras 3 fallos consecutivos y bloquea la siguiente llamada", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();

  // Agotar los 4 intentos (1 + 3 reintentos) tres veces para llegar a 3 fallos.
  // Dado que hay 4 intentos por llamada y el breaker cuenta LLAMADAS fallidas
  // (no intentos individuales), necesitamos hacer fallar callLLM 3 veces.
  const siempreFalla = stub(globalThis, "fetch", async () => new Response("err", { status: 500 }));

  for (let i = 0; i < 3; i++) {
    await assertRejects(() => callLLM({ system: "s", user: "u" }), Error);
  }
  siempreFalla.restore();

  // La cuarta llamada debe fallar inmediatamente (breaker abierto) sin tocar fetch.
  let fetchLlamado = false;
  using _f = stub(globalThis, "fetch", async () => { fetchLlamado = true; return makeOkResponse("ok"); });
  await assertRejects(
    () => callLLM({ system: "s", user: "u" }),
    Error,
    "circuit breaker abierto",
  );
  assertEquals(fetchLlamado, false);
});

Deno.test("callLLM: éxito limpia el contador de fallos consecutivos", async () => {
  Deno.env.set("LLM_API_KEY", "sk-test");
  _resetBreakerForTest();

  // 2 fallos → no abre breaker
  {
    using _f = stub(globalThis, "fetch", async () => new Response("err", { status: 500 }));
    for (let i = 0; i < 2; i++) {
      await assertRejects(() => callLLM({ system: "s", user: "u" }), Error);
    }
  }

  // 1 éxito → reinicia conteo
  {
    using _f = stub(globalThis, "fetch", async () => makeOkResponse("ok"));
    await callLLM({ system: "s", user: "u" });
  }

  // 2 fallos más no abren el breaker (el conteo se reinició)
  {
    using _f = stub(globalThis, "fetch", async () => new Response("err", { status: 500 }));
    for (let i = 0; i < 2; i++) {
      await assertRejects(() => callLLM({ system: "s", user: "u" }), Error);
    }
  }

  // Siguiente llamada exitosa debe pasar (breaker cerrado)
  {
    using _f = stub(globalThis, "fetch", async () => makeOkResponse("sin breaker"));
    const r = await callLLM({ system: "s", user: "u" });
    assertEquals(r.text, "sin breaker");
  }
});
