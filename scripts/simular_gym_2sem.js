// Simula 2 semanas de entrenamientos PREVIAS a tu primer registro real
// y las sube a Supabase respetando RLS (inicia sesión con tu usuario).
//
// Uso (PowerShell, desde la raíz del repo):
//   npm install @supabase/supabase-js          # solo la primera vez
//   $env:PRTS_EMAIL = "tu@correo.com"
//   $env:PRTS_PASSWORD = "tu-contraseña"
//   node scripts/simular_gym_2sem.js           # DRY-RUN: muestra qué generaría
//   node scripts/simular_gym_2sem.js --commit  # inserta en la base de datos
//
// Lógica de simulación:
//   - Toma tu sesión real MÁS ANTIGUA de cada ejercicio como línea base.
//   - Genera sesiones para los 14 días anteriores a tu primera sesión real,
//     siguiendo tu rutina semanal (routine_days); los días sin rutina descansan.
//   - Regresa los pesos ~2.5% por semana hacia atrás (redondeado a 0.5 kg)
//     y varía repeticiones dentro del rango del ejercicio (progresión creíble).
//   - No toca fechas que ya tengan sesión (unique user_id + session_date).

const fs = require("fs");
const path = require("path");
const { createClient } = require("@supabase/supabase-js");

// ---------- config ----------
const cfg = fs.readFileSync(path.join(__dirname, "..", "app", "config.js"), "utf8");
const URL = cfg.match(/SUPABASE_URL:\s*"([^"]+)"/)[1];
const KEY = cfg.match(/SUPABASE_ANON_KEY:\s*"([^"]+)"/)[1];
const EMAIL = process.env.PRTS_EMAIL;
const PASSWORD = process.env.PRTS_PASSWORD;
const COMMIT = process.argv.includes("--commit");

if (!EMAIL || !PASSWORD) {
  console.error("Define $env:PRTS_EMAIL y $env:PRTS_PASSWORD antes de ejecutar.");
  process.exit(1);
}

const sb = createClient(URL, KEY);
const r05 = (x) => Math.round(x * 2) / 2;            // redondeo a 0.5 kg
const fecha = (d) => d.toISOString().slice(0, 10);

(async () => {
  // ---------- login ----------
  const { error: authErr } = await sb.auth.signInWithPassword({ email: EMAIL, password: PASSWORD });
  if (authErr) { console.error("Login falló:", authErr.message); process.exit(1); }

  // ---------- 1. obtener registros existentes ----------
  const { data: sessions, error: e1 } = await sb.from("workout_sessions")
    .select("id, session_date, routine_day_id").order("session_date");
  if (e1) throw e1;
  if (!sessions.length) { console.error("No hay sesiones reales todavía; no hay línea base."); process.exit(1); }

  const { data: sets, error: e2 } = await sb.from("workout_sets")
    .select("session_id, exercise_id, set_number, weight_kg, reps");
  if (e2) throw e2;
  const { data: routineDays } = await sb.from("routine_days").select("id, weekday, name");
  const { data: routineExs } = await sb.from("routine_exercises")
    .select("routine_day_id, exercise_id, position, rep_min, rep_max").order("position");
  const { data: exercises } = await sb.from("exercises").select("id, name");
  const exName = Object.fromEntries(exercises.map(x => [x.id, x.name]));

  console.log(`Registros actuales: ${sessions.length} sesiones, ${sets.length} sets`);
  console.log(`Primera sesión real: ${sessions[0].session_date}\n`);

  // ---------- 2. línea base por ejercicio (su sesión real más antigua) ----------
  const ordenSesion = Object.fromEntries(sessions.map((s, i) => [s.id, i]));
  const baseline = {}; // exercise_id -> [{set_number, weight_kg, reps}]
  for (const ex of exercises) {
    const suyos = sets.filter(s => s.exercise_id === ex.id);
    if (!suyos.length) continue;
    const primeraSesion = suyos.reduce((min, s) =>
      ordenSesion[s.session_id] < ordenSesion[min.session_id] ? s : min).session_id;
    baseline[ex.id] = suyos.filter(s => s.session_id === primeraSesion)
      .sort((a, b) => a.set_number - b.set_number);
  }

  // ---------- 3. generar los 14 días previos ----------
  const fechasOcupadas = new Set(sessions.map(s => s.session_date));
  const inicio = new Date(sessions[0].session_date + "T12:00:00");
  const plan = [];

  for (let diasAtras = 14; diasAtras >= 1; diasAtras--) {
    const d = new Date(inicio); d.setDate(d.getDate() - diasAtras);
    const f = fecha(d);
    if (fechasOcupadas.has(f)) continue;                     // ya existe sesión real
    const rd = routineDays.find(x => x.weekday === d.getDay());
    if (!rd) continue;                                       // día de descanso
    const semanasAtras = diasAtras > 7 ? 2 : 1;

    const setsDia = [];
    for (const re of routineExs.filter(x => x.routine_day_id === rd.id)) {
      const base = baseline[re.exercise_id];
      if (!base) { console.log(`  (sin línea base para ${exName[re.exercise_id]}; se omite)`); continue; }
      for (const bs of base) {
        const peso = Math.max(2.5, r05(bs.weight_kg * (1 - 0.025 * semanasAtras)));
        let reps = bs.reps - (semanasAtras === 2 ? 1 : 0) - (Math.random() < 0.3 ? 1 : 0);
        reps = Math.min(re.rep_max, Math.max(re.rep_min, reps));
        setsDia.push({ exercise_id: re.exercise_id, set_number: bs.set_number, weight_kg: peso, reps });
      }
    }
    if (setsDia.length) plan.push({ session_date: f, routine_day_id: rd.id, name: rd.name, sets: setsDia });
  }

  // ---------- 4. resumen ----------
  for (const p of plan) {
    console.log(`${p.session_date}  ${p.name}  (${p.sets.length} sets)`);
    const porEj = {};
    for (const s of p.sets) (porEj[s.exercise_id] ??= []).push(`${s.weight_kg}kg×${s.reps}`);
    for (const [ex, lista] of Object.entries(porEj)) console.log(`    ${exName[ex]}: ${lista.join(", ")}`);
  }
  const totalSets = plan.reduce((a, p) => a + p.sets.length, 0);
  console.log(`\nTotal a crear: ${plan.length} sesiones, ${totalSets} sets`);

  if (!COMMIT) { console.log("\nDRY-RUN: nada insertado. Ejecuta con --commit para subir."); return; }

  // ---------- 5. subir ----------
  for (const p of plan) {
    const { data: ses, error: eS } = await sb.from("workout_sessions")
      .insert({ session_date: p.session_date, routine_day_id: p.routine_day_id, notes: "simulada (backfill 2 semanas)" })
      .select("id").single();
    if (eS) { console.error(`Error en ${p.session_date}:`, eS.message); continue; }
    const { error: eK } = await sb.from("workout_sets")
      .insert(p.sets.map(s => ({ ...s, session_id: ses.id })));
    if (eK) console.error(`  sets de ${p.session_date}:`, eK.message);
    else console.log(`✓ ${p.session_date} ${p.name}`);
  }
  console.log("\nListo. Revisa las gráficas de progresión en el módulo Gym.");
})().catch(e => { console.error(e); process.exit(1); });
