# Sistema Personal de Organización (PRTS)

Sistema integral para gestionar tres roles: estudiante (TecNM Celaya), instructor (Wolves robótica / LevelUp idiomas) y vida personal (salud, finanzas).

**Estado actual:** Fase 0–1 · Corte vertical del módulo **Gym** en producción.

## Estructura

```
app/                  App web (módulo Gym v0, vanilla JS + Supabase)
docs/                 Documentación técnica y prototipo visual original
supabase/migrations/  Migraciones SQL versionadas
```

## Puesta en marcha

1. **Supabase**: crear proyecto en supabase.com, luego aplicar la migración:
   - Opción A (dashboard): SQL Editor → pegar `supabase/migrations/20260610000001_gym_schema.sql` → Run.
   - Opción B (CLI): `npx supabase link --project-ref <ref>` y `npx supabase db push`.
2. **Config**: copiar URL y anon key (Project Settings → API) en `app/config.js`.
3. **Usuario**: en el dashboard → Authentication → Add user (o usar "Crear cuenta" en la app).
4. **Local**: abrir `app/index.html` con Live Server (VS Code) o `npx serve app`.
5. **Deploy**: conectar el repo a Vercel con root directory `app/`.

La primera vez que inicies sesión, la app carga automáticamente la rutina (Leg/Push/Pull A-B) como datos semilla.

## Plan de fases

Ver `docs/Documentacion_Sistema_PRTS.docx` — plan completo de 6 fases (Fundaciones → Persistencia → Mobile/Offline → Integraciones → Jarvis → Refinamiento).
