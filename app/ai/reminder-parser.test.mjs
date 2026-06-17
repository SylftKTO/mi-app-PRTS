// Tests para la lógica de parseRecordatorio de actions.js — correr con:
//   node --test app/ai/reminder-parser.test.mjs
//
// NOTA: las funciones parseRecordatorio y limpiarTitulo están duplicadas aquí
// desde actions.js (son puras, sin DOM). Si se cambian en actions.js, actualizar
// también aquí. Objetivo: reemplazar esta copia cuando actions.js se refactorice
// a ES module.
import { test } from "node:test";
import assert from "node:assert/strict";

// ─── Funciones copiadas de actions.js (líneas ~202-268) ─────────────────────

const DIAS_SEM = { domingo: 0, lunes: 1, martes: 2, miércoles: 3, miercoles: 3, jueves: 4, viernes: 5, sábado: 6, sabado: 6 };

function limpiarTitulo(s) {
  return s.replace(/\b(a las?|el|la|los|las|de|del|para|que|este|esta)\b/gi, " ")
    .replace(/\s{2,}/g, " ").replace(/^[\s,.:;-]+|[\s,.:;-]+$/g, "").trim();
}

function parseRecordatorio(t) {
  const mm = t.match(/^(?:recu[ée]rdame|recuerdame|recu[ée]rda|recordatorio(?:\sde)?)\s+(?:de\s+|que\s+)?(.+)$/i);
  if (!mm) return null;
  let resto = mm[1].trim();
  const now = new Date();
  const cap = (s) => s ? s[0].toUpperCase() + s.slice(1) : s;

  let r = resto.match(/\ben\s+(\d+)\s*(min(?:uto)?s?|h(?:ora)?s?|d[ií]as?)\b/i);
  if (r) {
    const n = +r[1], u = r[2].toLowerCase(), at = new Date(now);
    if (/^min/.test(u)) at.setMinutes(at.getMinutes() + n);
    else if (/^h/.test(u)) at.setHours(at.getHours() + n);
    else at.setDate(at.getDate() + n);
    const title = cap(limpiarTitulo(resto.replace(r[0], " ")));
    return title ? { remind_at: at.toISOString(), title } : null;
  }

  const base = new Date(now); base.setSeconds(0, 0);
  let diaFijado = false;
  if (/\bpasado\s+ma[ñn]ana\b/i.test(resto)) { base.setDate(base.getDate() + 2); resto = resto.replace(/\bpasado\s+ma[ñn]ana\b/i, " "); diaFijado = true; }
  else if (/\bma[ñn]ana\b/i.test(resto)) { base.setDate(base.getDate() + 1); resto = resto.replace(/\bma[ñn]ana\b/i, " "); diaFijado = true; }
  else if (/\bhoy\b/i.test(resto)) { resto = resto.replace(/\bhoy\b/i, " "); diaFijado = true; }

  r = resto.match(/\b(?:el\s+)?(domingo|lunes|martes|mi[eé]rcoles|jueves|viernes|s[áa]bado)\b/i);
  if (r) {
    const k = r[1].toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    const target = DIAS_SEM[k];
    if (target != null) { let diff = (target - base.getDay() + 7) % 7; if (diff === 0) diff = 7; base.setDate(base.getDate() + diff); diaFijado = true; resto = resto.replace(r[0], " "); }
  }
  r = resto.match(/\bel\s+(?:d[ií]a\s+)?(\d{1,2})\b/i);
  if (r) {
    const dia = +r[1];
    if (dia >= 1 && dia <= 31) { base.setDate(dia); if (base < now) base.setMonth(base.getMonth() + 1); diaFijado = true; resto = resto.replace(r[0], " "); }
  }

  let h = null, min = 0, horaFijada = false;
  r = resto.match(/\ba\s+la(?:s)?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|de la ma[ñn]ana|de la tarde|de la noche|hrs?|horas)?/i)
    || resto.match(/\b(\d{1,2}):(\d{2})\s*(am|pm)?\b/i)
    || resto.match(/\b(\d{1,2})\s*(am|pm)\b/i);
  if (r) {
    h = +r[1]; min = r[2] ? +r[2] : 0;
    const suf = (r[3] || r[2] || "").toString().toLowerCase();
    if (/pm|p\.m\.|tarde|noche/.test(suf) && h < 12) h += 12;
    else if (/(am|a\.m\.|ma[ñn]ana)/.test(suf) && h === 12) h = 0;
    else if (!suf && h >= 1 && h <= 7) h += 12;
    if (h >= 0 && h <= 23) { horaFijada = true; resto = resto.replace(r[0], " "); }
    else h = null;
  }

  let at;
  if (horaFijada) {
    at = new Date(base); at.setHours(h, min, 0, 0);
    if (!diaFijado && at < now) at.setDate(at.getDate() + 1);
  } else if (diaFijado) {
    at = new Date(base); at.setHours(9, 0, 0, 0);
  } else {
    at = new Date(now.getTime() + 60 * 60000);
  }
  const title = cap(limpiarTitulo(resto));
  return title ? { remind_at: at.toISOString(), title } : null;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Devuelve la diferencia en minutos entre dos fechas ISO. */
function diffMinutes(isoA, isoB) {
  return Math.round((new Date(isoA) - new Date(isoB)) / 60000);
}

function assertHour(isoDate, expectedHour, expectedMin = 0) {
  const d = new Date(isoDate);
  assert.equal(d.getHours(), expectedHour, `hora esperada ${expectedHour}, obtenida ${d.getHours()} en ${isoDate}`);
  assert.equal(d.getMinutes(), expectedMin, `minutos esperados ${expectedMin}, obtenidos ${d.getMinutes()}`);
}

function assertDayOffset(isoDate, expectedOffset) {
  const today = new Date();
  const d = new Date(isoDate);
  today.setHours(0, 0, 0, 0);
  const target = new Date(today);
  target.setDate(target.getDate() + expectedOffset);
  assert.equal(d.getDate(), target.getDate(), `día del mes esperado ${target.getDate()}, obtenido ${d.getDate()}`);
}

// ─── Sin prefijo de recordatorio → null ──────────────────────────────────────

test("parseRecordatorio: texto sin prefijo → null", () => {
  assert.equal(parseRecordatorio("comprar creatina mañana"), null);
});

test("parseRecordatorio: solo el prefijo sin título → null", () => {
  assert.equal(parseRecordatorio("recuérdame"), null);
});

// ─── Tiempos relativos ────────────────────────────────────────────────────────

test("parseRecordatorio: en 30 minutos", () => {
  const before = Date.now();
  const r = parseRecordatorio("recuérdame tomar medicamento en 30 minutos");
  assert.notEqual(r, null);
  const diff = diffMinutes(r.remind_at, new Date(before));
  assert.ok(diff >= 29 && diff <= 31, `esperaba ~30 min, obtuvo ${diff}`);
  assert.ok(r.title.toLowerCase().includes("tomar"), `título: ${r.title}`);
});

test("parseRecordatorio: en 2 horas", () => {
  const before = Date.now();
  const r = parseRecordatorio("recuérdame llamar al doctor en 2 horas");
  assert.notEqual(r, null);
  const diff = diffMinutes(r.remind_at, new Date(before));
  assert.ok(diff >= 119 && diff <= 121, `esperaba ~120 min, obtuvo ${diff}`);
});

test("parseRecordatorio: en 3 días", () => {
  const r = parseRecordatorio("recuérdame entregar el reporte en 3 días");
  assert.notEqual(r, null);
  assertDayOffset(r.remind_at, 3);
});

test("parseRecordatorio: abreviación 'min'", () => {
  const before = Date.now();
  const r = parseRecordatorio("recuérdame revisar correo en 10 min");
  assert.notEqual(r, null);
  const diff = diffMinutes(r.remind_at, new Date(before));
  assert.ok(diff >= 9 && diff <= 11, `esperaba ~10 min, obtuvo ${diff}`);
});

test("parseRecordatorio: abreviación 'h' para horas", () => {
  const before = Date.now();
  const r = parseRecordatorio("recuérdame ejercicio en 1h");
  assert.notEqual(r, null);
  const diff = diffMinutes(r.remind_at, new Date(before));
  assert.ok(diff >= 59 && diff <= 61, `esperaba ~60 min, obtuvo ${diff}`);
});

// ─── Días nombrados ───────────────────────────────────────────────────────────

test("parseRecordatorio: mañana a las 9am", () => {
  const r = parseRecordatorio("recuérdame llamar a mamá mañana a las 9 am");
  assert.notEqual(r, null);
  assertDayOffset(r.remind_at, 1);
  assertHour(r.remind_at, 9, 0);
});

test("parseRecordatorio: pasado mañana", () => {
  const r = parseRecordatorio("recuérdame pagar renta pasado mañana");
  assert.notEqual(r, null);
  assertDayOffset(r.remind_at, 2);
  assertHour(r.remind_at, 9, 0);  // sin hora → 9:00
});

test("parseRecordatorio: hoy con hora explícita", () => {
  const r = parseRecordatorio("recuérdame tomar agua hoy a las 8 pm");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 20, 0);
});

// ─── Hora con distintos sufijos ───────────────────────────────────────────────

test("parseRecordatorio: 'a las 3 pm' → 15:00", () => {
  const r = parseRecordatorio("recuérdame la clase a las 3 pm");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 15, 0);
});

test("parseRecordatorio: 'a las 3' sin sufijo y h <= 7 → PM (15:00)", () => {
  const r = parseRecordatorio("recuérdame la reunión a las 3");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 15, 0);
});

test("parseRecordatorio: 'a las 9' sin sufijo y h > 7 → mantiene 9:00 (AM)", () => {
  const r = parseRecordatorio("recuérdame desayuno a las 9");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 9, 0);
});

test("parseRecordatorio: '10:30 am'", () => {
  const r = parseRecordatorio("recuérdame junta a las 10:30 am");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 10, 30);
});

test("parseRecordatorio: 'de la tarde' → PM", () => {
  const r = parseRecordatorio("recuérdame estudiar a las 4 de la tarde");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 16, 0);
});

test("parseRecordatorio: 'de la noche' → PM si h < 12", () => {
  const r = parseRecordatorio("recuérdame dormir a las 10 de la noche");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 22, 0);
});

test("parseRecordatorio: '12 pm' → 12:00 (mediodía, sin sumar 12)", () => {
  const r = parseRecordatorio("recuérdame almorzar a las 12 pm");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 12, 0);
});

test("parseRecordatorio: '12 am' → 0:00 (medianoche)", () => {
  const r = parseRecordatorio("recuérdame revisar alarma a las 12 am");
  assert.notEqual(r, null);
  assertHour(r.remind_at, 0, 0);
});

// ─── Día del mes ──────────────────────────────────────────────────────────────

test("parseRecordatorio: 'el día 15' → día 15 del mes", () => {
  const r = parseRecordatorio("recuérdame pagar factura el día 15");
  assert.notEqual(r, null);
  assert.equal(new Date(r.remind_at).getDate(), 15);
});

test("parseRecordatorio: 'el 20' → día 20 del mes", () => {
  const r = parseRecordatorio("recuérdame comprar proteína el 20");
  assert.notEqual(r, null);
  assert.equal(new Date(r.remind_at).getDate(), 20);
});

test("parseRecordatorio: día ya pasado en el mes actual → avanza al siguiente mes", () => {
  // Forzar que el día 1 sea siempre en el pasado
  const r = parseRecordatorio("recuérdame hacer reporte el día 1");
  assert.notEqual(r, null);
  const d = new Date(r.remind_at);
  const hoy = new Date();
  // Debe ser el día 1 del siguiente mes si el 1 ya pasó este mes
  if (hoy.getDate() > 1) {
    const mesEsperado = (hoy.getMonth() + 1) % 12;
    assert.equal(d.getMonth(), mesEsperado);
  }
  assert.equal(d.getDate(), 1);
});

// ─── Sin fecha/hora → en 1 hora ──────────────────────────────────────────────

test("parseRecordatorio: sin fecha ni hora → en ~1 hora", () => {
  const before = Date.now();
  const r = parseRecordatorio("recuérdame comprar creatina");
  assert.notEqual(r, null);
  const diff = diffMinutes(r.remind_at, new Date(before));
  assert.ok(diff >= 59 && diff <= 61, `esperaba ~60 min, obtuvo ${diff}`);
});

// ─── Título limpio ────────────────────────────────────────────────────────────

test("parseRecordatorio: título se capitaliza", () => {
  const r = parseRecordatorio("recuérdame estudiar control en 2 horas");
  assert.notEqual(r, null);
  assert.equal(r.title[0], r.title[0].toUpperCase());
});

test("parseRecordatorio: preposiciones se eliminan del título", () => {
  const r = parseRecordatorio("recuérdame tomar la pastilla de la mañana");
  assert.notEqual(r, null);
  // "la" y "de" deben haber sido eliminados o el título no los incluye como extremos
  assert.ok(!r.title.startsWith("la ") && !r.title.startsWith("de "), `título: ${r.title}`);
});

test("parseRecordatorio: variante 'recuerdame' sin tilde", () => {
  const r = parseRecordatorio("recuerdame tomar agua en 1 hora");
  assert.notEqual(r, null);
  assert.ok(r.title.toLowerCase().includes("tomar"), `título: ${r.title}`);
});

test("parseRecordatorio: prefijo 'recordatorio de'", () => {
  const r = parseRecordatorio("recordatorio de entregar tarea mañana");
  assert.notEqual(r, null);
  assertDayOffset(r.remind_at, 1);
});
