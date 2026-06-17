// Tests unitarios para schemas.ts — correr con:
//   deno test supabase/functions/_shared/schemas.test.ts
import { assertEquals, assertStrictEquals, assertNotEquals } from "jsr:@std/assert";
import { parseJSON, validateInbox, validateCommand, validateInsights } from "./schemas.ts";

// ─── parseJSON ──────────────────────────────────────────────────────────────

Deno.test("parseJSON: extrae objeto JSON plano", () => {
  assertEquals(parseJSON('{"a":1}'), { a: 1 });
});

Deno.test("parseJSON: extrae JSON con fence markdown ```json", () => {
  assertEquals(parseJSON("```json\n{\"a\":1}\n```"), { a: 1 });
});

Deno.test("parseJSON: extrae JSON con fence ``` sin lenguaje", () => {
  assertEquals(parseJSON("```\n{\"x\":\"y\"}\n```"), { x: "y" });
});

Deno.test("parseJSON: extrae primer objeto de texto mixto", () => {
  assertEquals(parseJSON('Aquí la respuesta: {"ok":true} más texto'), { ok: true });
});

Deno.test("parseJSON: devuelve null si no hay JSON", () => {
  assertStrictEquals(parseJSON("sin JSON aquí"), null);
});

Deno.test("parseJSON: devuelve null con JSON inválido", () => {
  assertStrictEquals(parseJSON("{clave sin comillas: 1}"), null);
});

Deno.test("parseJSON: maneja string vacío", () => {
  assertStrictEquals(parseJSON(""), null);
});

Deno.test("parseJSON: extrae objeto anidado", () => {
  assertEquals(parseJSON('{"a":{"b":2}}'), { a: { b: 2 } });
});

// ─── validateInbox ──────────────────────────────────────────────────────────

Deno.test("validateInbox: tarea mínima válida", () => {
  const r = validateInbox({ module: "tareas", action: "create", payload: { title: "Entregar reporte" }, confidence: 0.9, summary: "Tarea nueva" });
  assertNotEquals(r, null);
  assertEquals(r!.module, "tareas");
  assertEquals(r!.payload.title, "Entregar reporte");
  assertEquals(r!.payload.origin, "personal");   // default
  assertEquals(r!.payload.priority, "media");    // default
  assertStrictEquals(r!.payload.deadline, null); // default
});

Deno.test("validateInbox: tarea con todos los campos explícitos", () => {
  const r = validateInbox({ module: "tareas", action: "create",
    payload: { title: "Examen", origin: "escuela", priority: "alta", deadline: "2025-06-01" },
    confidence: 0.95, summary: "Examen de control" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.origin, "escuela");
  assertEquals(r!.payload.priority, "alta");
  assertEquals(r!.payload.deadline, "2025-06-01");
});

Deno.test("validateInbox: tarea sin title → null", () => {
  assertStrictEquals(validateInbox({ module: "tareas", action: "create", payload: {}, confidence: 0.9, summary: "x" }), null);
});

Deno.test("validateInbox: tarea con origin inválido → fallback personal", () => {
  const r = validateInbox({ module: "tareas", action: "create",
    payload: { title: "T", origin: "trabajo" }, confidence: 0.8, summary: "x" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.origin, "personal");
});

Deno.test("validateInbox: tarea con deadline con formato inválido → null deadline", () => {
  const r = validateInbox({ module: "tareas", action: "create",
    payload: { title: "T", deadline: "01/06/2025" }, confidence: 0.8, summary: "x" });
  assertNotEquals(r, null);
  assertStrictEquals(r!.payload.deadline, null);
});

Deno.test("validateInbox: recordatorio válido con deadline", () => {
  const r = validateInbox({ module: "recordatorio", action: "create",
    payload: { title: "Comprar creatina", deadline: "2025-07-01" }, confidence: 0.85, summary: "Recordatorio" });
  assertNotEquals(r, null);
  assertEquals(r!.module, "recordatorio");
  assertEquals(r!.payload.title, "Comprar creatina");
});

Deno.test("validateInbox: recordatorio sin title → null", () => {
  assertStrictEquals(validateInbox({ module: "recordatorio", action: "create", payload: {}, confidence: 0.9, summary: "x" }), null);
});

Deno.test("validateInbox: dieta válida con todos los macros", () => {
  const r = validateInbox({ module: "dieta", action: "create",
    payload: { name: "Pechuga asada", meal: "cena", kcal: 300, protein_g: 40, carbs_g: 0, fat_g: 8 },
    confidence: 0.9, summary: "Cena registrada" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.name, "Pechuga asada");
  assertEquals(r!.payload.meal, "cena");
  assertEquals(r!.payload.kcal, 300);
});

Deno.test("validateInbox: dieta con macros negativos → corregidos a 0", () => {
  const r = validateInbox({ module: "dieta", action: "create",
    payload: { name: "Algo", meal: "desayuno", kcal: -100, protein_g: -5, carbs_g: 0, fat_g: 0 },
    confidence: 0.8, summary: "x" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.kcal, 0);
  assertEquals(r!.payload.protein_g, 0);
});

Deno.test("validateInbox: dieta con meal inválida → null", () => {
  assertStrictEquals(validateInbox({ module: "dieta", action: "create",
    payload: { name: "X", meal: "merienda" }, confidence: 0.8, summary: "x" }), null);
});

Deno.test("validateInbox: dieta sin name → null", () => {
  assertStrictEquals(validateInbox({ module: "dieta", action: "create",
    payload: { meal: "cena" }, confidence: 0.8, summary: "x" }), null);
});

Deno.test("validateInbox: apunte con subject válido", () => {
  const r = validateInbox({ module: "apuntes", action: "create",
    payload: { subject: "Control", topic: "PID", summary: "Controlador..." },
    confidence: 0.9, summary: "Apunte de control" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.subject, "Control");
});

Deno.test("validateInbox: apunte sin subject ni topic → null", () => {
  assertStrictEquals(validateInbox({ module: "apuntes", action: "create",
    payload: { summary: "Solo resumen" }, confidence: 0.8, summary: "x" }), null);
});

Deno.test("validateInbox: proyecto válido", () => {
  const r = validateInbox({ module: "proyectos", action: "create",
    payload: { name: "Brazo robótico", due_date: "2025-09-01" },
    confidence: 0.9, summary: "Nuevo proyecto" });
  assertNotEquals(r, null);
  assertEquals(r!.payload.name, "Brazo robótico");
});

Deno.test("validateInbox: proyecto sin name → null", () => {
  assertStrictEquals(validateInbox({ module: "proyectos", action: "create",
    payload: {}, confidence: 0.8, summary: "x" }), null);
});

Deno.test("validateInbox: gym con action create → null (no se acepta)", () => {
  assertStrictEquals(validateInbox({ module: "gym", action: "create",
    payload: {}, confidence: 0.9, summary: "x" }), null);
});

Deno.test("validateInbox: desconocido con action none → válido", () => {
  const r = validateInbox({ module: "desconocido", action: "none",
    payload: {}, confidence: 0.3, summary: "No entendí" });
  assertNotEquals(r, null);
  assertEquals(r!.module, "desconocido");
  assertEquals(r!.action, "none");
});

Deno.test("validateInbox: módulo no válido → null", () => {
  assertStrictEquals(validateInbox({ module: "finanzas", action: "none",
    payload: {}, confidence: 0.5, summary: "x" }), null);
});

Deno.test("validateInbox: confidence fuera de rango → null", () => {
  assertStrictEquals(validateInbox({ module: "tareas", action: "create",
    payload: { title: "T" }, confidence: 1.5, summary: "x" }), null);
  assertStrictEquals(validateInbox({ module: "tareas", action: "create",
    payload: { title: "T" }, confidence: -0.1, summary: "x" }), null);
});

Deno.test("validateInbox: summary vacío → null", () => {
  assertStrictEquals(validateInbox({ module: "tareas", action: "create",
    payload: { title: "T" }, confidence: 0.9, summary: "  " }), null);
});

Deno.test("validateInbox: raw no es objeto → null", () => {
  assertStrictEquals(validateInbox("string"), null);
  assertStrictEquals(validateInbox(null), null);
  assertStrictEquals(validateInbox([]), null);
});

// ─── validateCommand ─────────────────────────────────────────────────────────

Deno.test("validateCommand: open spotify válido con URI", () => {
  const r = validateCommand({ intent: "open", params: { target: "spotify", deep_link: "spotify:playlist:abc" },
    speak: "Abriendo playlist.", confidence: 0.95 });
  assertNotEquals(r, null);
  assertEquals(r!.intent, "open");
  assertEquals(r!.params.deep_link, "spotify:playlist:abc");
});

Deno.test("validateCommand: open spotify con link web válido", () => {
  const r = validateCommand({ intent: "open",
    params: { target: "spotify", deep_link: "https://open.spotify.com/playlist/abc" },
    speak: "", confidence: 0.9 });
  assertNotEquals(r, null);
});

Deno.test("validateCommand: open sin target spotify → null", () => {
  assertStrictEquals(validateCommand({ intent: "open",
    params: { target: "youtube", deep_link: "https://youtube.com" },
    speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: open con deep_link prohibido → null", () => {
  assertStrictEquals(validateCommand({ intent: "open",
    params: { target: "spotify", deep_link: "https://evil.com" },
    speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: navigate a vista válida", () => {
  const r = validateCommand({ intent: "navigate", params: { view: "gym" }, speak: "Abriendo gym.", confidence: 1 });
  assertNotEquals(r, null);
  assertEquals(r!.params.view, "gym");
});

Deno.test("validateCommand: navigate a vista inválida → null", () => {
  assertStrictEquals(validateCommand({ intent: "navigate", params: { view: "finanzas" },
    speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: summary sin scope → fallback dia", () => {
  const r = validateCommand({ intent: "summary", params: {}, speak: "", confidence: 0.8 });
  assertNotEquals(r, null);
  assertEquals(r!.params.scope, "dia");
});

Deno.test("validateCommand: summary con scope válido gym", () => {
  const r = validateCommand({ intent: "summary", params: { scope: "gym" }, speak: "", confidence: 0.8 });
  assertNotEquals(r, null);
  assertEquals(r!.params.scope, "gym");
});

Deno.test("validateCommand: create_task válida con defaults", () => {
  const r = validateCommand({ intent: "create_task", params: { title: "Estudiar control" },
    speak: "Tarea creada.", confidence: 0.95 });
  assertNotEquals(r, null);
  assertEquals(r!.params.origin, "personal");
  assertEquals(r!.params.priority, "media");
  assertStrictEquals(r!.params.deadline, null);
});

Deno.test("validateCommand: create_task sin title → null", () => {
  assertStrictEquals(validateCommand({ intent: "create_task", params: {}, speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: create_task con title en blanco → null", () => {
  assertStrictEquals(validateCommand({ intent: "create_task", params: { title: "   " }, speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: log_weight válido", () => {
  const r = validateCommand({ intent: "log_weight", params: { weight_kg: 78.5 }, speak: "Registrado.", confidence: 1 });
  assertNotEquals(r, null);
  assertEquals(r!.params.weight_kg, 78.5);
});

Deno.test("validateCommand: log_weight con peso 0 → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_weight", params: { weight_kg: 0 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_weight con peso > 400 → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_weight", params: { weight_kg: 401 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_weight en límite 400 → válido", () => {
  assertNotEquals(validateCommand({ intent: "log_weight", params: { weight_kg: 400 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_set válido", () => {
  const r = validateCommand({ intent: "log_set",
    params: { exercise: "Press banca", weight_kg: 80, reps: 8 },
    speak: "Serie registrada.", confidence: 1 });
  assertNotEquals(r, null);
  assertEquals(r!.params.exercise, "Press banca");
  assertEquals(r!.params.reps, 8);
});

Deno.test("validateCommand: log_set sin exercise → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_set",
    params: { weight_kg: 80, reps: 8 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_set con weight_kg > 500 → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_set",
    params: { exercise: "Peso muerto", weight_kg: 501, reps: 1 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_set con reps 0 → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_set",
    params: { exercise: "Sentadilla", weight_kg: 100, reps: 0 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_set con reps 100 → válido (límite)", () => {
  assertNotEquals(validateCommand({ intent: "log_set",
    params: { exercise: "Curl", weight_kg: 10, reps: 100 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: log_set con reps > 100 → null", () => {
  assertStrictEquals(validateCommand({ intent: "log_set",
    params: { exercise: "Curl", weight_kg: 10, reps: 101 }, speak: "", confidence: 1 }), null);
});

Deno.test("validateCommand: weather sin location → válido con null", () => {
  const r = validateCommand({ intent: "weather", params: { location: null }, speak: "", confidence: 0.9 });
  assertNotEquals(r, null);
  assertStrictEquals(r!.params.location, null);
});

Deno.test("validateCommand: weather con location string → válido", () => {
  const r = validateCommand({ intent: "weather", params: { location: "Celaya" }, speak: "", confidence: 0.9 });
  assertNotEquals(r, null);
  assertEquals(r!.params.location, "Celaya");
});

Deno.test("validateCommand: weather con location número → se normaliza a null", () => {
  const r = validateCommand({ intent: "weather", params: { location: 123 }, speak: "", confidence: 0.9 });
  assertNotEquals(r, null);
  assertStrictEquals(r!.params.location, null);
});

Deno.test("validateCommand: ask con speak válido", () => {
  const r = validateCommand({ intent: "ask", params: {}, speak: "Cien años de soledad lo escribió Gabriel García Márquez.", confidence: 0.99 });
  assertNotEquals(r, null);
  assertEquals(r!.intent, "ask");
});

Deno.test("validateCommand: ask con speak vacío → null", () => {
  assertStrictEquals(validateCommand({ intent: "ask", params: {}, speak: "  ", confidence: 0.9 }), null);
});

Deno.test("validateCommand: unknown válido (sin params obligatorios)", () => {
  const r = validateCommand({ intent: "unknown", params: {}, speak: "No entendí el comando.", confidence: 0.1 });
  assertNotEquals(r, null);
  assertEquals(r!.intent, "unknown");
});

Deno.test("validateCommand: intent fuera del vocabulario → null", () => {
  assertStrictEquals(validateCommand({ intent: "delete_all", params: {}, speak: "", confidence: 0.9 }), null);
});

Deno.test("validateCommand: raw no es objeto → null", () => {
  assertStrictEquals(validateCommand(null), null);
  assertStrictEquals(validateCommand("texto"), null);
  assertStrictEquals(validateCommand(42), null);
});

Deno.test("validateCommand: confidence NaN → null", () => {
  assertStrictEquals(validateCommand({ intent: "unknown", params: {}, speak: "", confidence: NaN }), null);
});

// ─── validateInsights ────────────────────────────────────────────────────────

Deno.test("validateInsights: lista válida de 2 hallazgos", () => {
  const r = validateInsights({ items: [
    { kind: "gym", title: "Progreso en press banca", detail: "Subiste 5 kg este mes." },
    { kind: "peso", title: "Peso estable", detail: "Variación mínima." },
  ]});
  assertNotEquals(r, null);
  assertEquals(r!.length, 2);
  assertEquals(r![0].kind, "gym");
});

Deno.test("validateInsights: kind inválido → reemplazado por general", () => {
  const r = validateInsights({ items: [
    { kind: "desconocido", title: "Algo", detail: "Detalle." },
  ]});
  assertNotEquals(r, null);
  assertEquals(r![0].kind, "general");
});

Deno.test("validateInsights: 6 hallazgos → válido (límite máximo)", () => {
  const items = Array.from({ length: 6 }, (_, i) => ({
    kind: "general", title: `Título ${i}`, detail: "Detalle."
  }));
  assertNotEquals(validateInsights({ items }), null);
});

Deno.test("validateInsights: 7 hallazgos → null (excede límite)", () => {
  const items = Array.from({ length: 7 }, (_, i) => ({
    kind: "general", title: `Título ${i}`, detail: "Detalle."
  }));
  assertStrictEquals(validateInsights({ items }), null);
});

Deno.test("validateInsights: 0 hallazgos → null", () => {
  assertStrictEquals(validateInsights({ items: [] }), null);
});

Deno.test("validateInsights: item sin title → null", () => {
  assertStrictEquals(validateInsights({ items: [{ kind: "gym", detail: "Detalle." }] }), null);
});

Deno.test("validateInsights: item sin detail → null", () => {
  assertStrictEquals(validateInsights({ items: [{ kind: "gym", title: "Título" }] }), null);
});

Deno.test("validateInsights: title vacío → null", () => {
  assertStrictEquals(validateInsights({ items: [{ kind: "gym", title: "  ", detail: "Detalle." }] }), null);
});

Deno.test("validateInsights: raw sin campo items → null", () => {
  assertStrictEquals(validateInsights({ hallazgos: [{ kind: "gym", title: "T", detail: "D" }] }), null);
});

Deno.test("validateInsights: raw es array (no objeto) → null", () => {
  assertStrictEquals(validateInsights([{ kind: "gym", title: "T", detail: "D" }]), null);
});

Deno.test("validateInsights: items no es array → null", () => {
  assertStrictEquals(validateInsights({ items: "no es array" }), null);
});

Deno.test("validateInsights: title y detail se trimmean", () => {
  const r = validateInsights({ items: [{ kind: "dieta", title: "  Proteína alta  ", detail: "  Buen consumo.  " }] });
  assertNotEquals(r, null);
  assertEquals(r![0].title, "Proteína alta");
  assertEquals(r![0].detail, "Buen consumo.");
});
