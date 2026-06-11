# Product

## Register

product

## Users

Sergio (Sylft): estudiante de ingeniería en TecNM Celaya, instructor en Wolves (robótica) y LevelUp (idiomas), y atleta de gimnasio. Usuario único del sistema. Contexto de uso: el módulo Gym se usa **desde el teléfono, en el gimnasio, entre series** — una mano, prisa, luz artificial. El módulo Tareas se usa en ráfagas cortas de captura y revisión durante el día.

## Product Purpose

PRTS / SYLFT es el sistema personal de organización de Sergio: una sola app que cubre sus tres roles (estudiante, instructor, vida personal). Fase 1: módulos Gym (registro de entrenamiento PPL con sobrecarga progresiva) y Tareas (captura rápida con origen/prioridad/deadline). Éxito = registrar una serie o una tarea en menos de 5 segundos, y que el progreso sea visible sin esfuerzo.

## Brand Personality

Sobrio, ordenado, personal. "Tu sistema, en orden." Estética de biblioteca privada / cuaderno de ingeniero: navy profundo, serif elegante para títulos y cifras, etiquetas monospace en mayúsculas, acento azul acero único. Calma y control, nunca gamificación ruidosa.

## Anti-references

- El dark theme de GitHub (paleta actual heredada: #0d1117 + naranja #f78166) — genérico, sin identidad.
- Apps fitness gamificadas (Strong, Hevy con confetti, anillos, colores neón).
- Dashboards SaaS con gradientes, glassmorphism o tarjetas-héroe con métricas gigantes.

## Design Principles

1. **Una mano, entre series**: cada acción frecuente del Gym (registrar kg×reps) debe completarse con el pulgar en segundos; inputs grandes, referencia de la última sesión siempre visible.
2. **El dato manda**: cifras en serif claro, etiquetas en mono; el color acento señala estado (progreso, récord, urgencia), nunca decora.
3. **Un solo idioma visual**: Gym, Tareas y futuros módulos comparten tokens (styles.css); mismo botón, misma tarjeta, misma etiqueta en todas las pantallas.
4. **Progreso visible sin pedirlo**: última sesión, estancamiento y récords aparecen en contexto, no escondidos en una pestaña.

## Accessibility & Inclusion

- Contraste AA mínimo (4.5:1 texto normal) sobre fondos navy.
- Targets táctiles ≥ 44px en el Gym (se usa con manos sudadas).
- `prefers-reduced-motion` respetado; el motion solo comunica estado.
- Idioma: español (es-MX).
