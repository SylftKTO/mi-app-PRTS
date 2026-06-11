# Design — SYLFT / PRTS

Sistema visual derivado del prototipo de dashboard (`docs/Dashboard prototipe.png`) y del logo (`docs/Logo.png`). Fuente de verdad en código: `app/styles.css`.

## Theme

Dark único (no hay modo claro). Navy profundo casi negro; superficies apenas un paso más claras; bordes hairline. La calidez la pone la tipografía serif, no el color.

## Color Palette

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#0B0D12` | Fondo de página |
| `--surface` | `#10131A` | Tarjetas, paneles |
| `--surface-2` | `#171B25` | Inputs, hover, capa secundaria |
| `--line` | `#1E2330` | Bordes hairline |
| `--text` | `#E8EAF1` | Texto principal |
| `--muted` | `#9AA1B3` | Texto secundario |
| `--faint` | `#62687A` | Etiquetas, metadatos |
| `--accent` | `#8FAEDC` | Azul acero claro: cifras destacadas, progreso, selección |
| `--accent-deep` | `#4E6FA8` | Relleno de checkboxes, botones primarios |
| `--ok` | `#85C49E` | Éxito / serie completada |
| `--warn` | `#D9A763` | Estancamiento, deadlines próximos |
| `--danger` | `#D9786C` | Vencido, eliminar |

Estrategia **restrained**: un solo acento azul acero; verde/ámbar/rojo solo como semántica de estado.

## Typography

- **Display y cifras**: `Source Serif 4` (300–600). Títulos de pantalla, números grandes, nombres de día.
- **Cuerpo y UI**: `Inter` (400–600). Labels de formularios, botones, texto corrido.
- **Etiquetas técnicas**: `JetBrains Mono` (400–500), MAYÚSCULAS, tracking `.14em–.2em`, 10–11px. Fechas, categorías, metadatos, ejes de gráficas.

## Components

- **Tarjeta**: `--surface`, borde 1px `--line`, radio 14px, padding 14–16px. Sin sombras fuertes, sin nesting.
- **Stat card** (patrón del dashboard): guion corto arriba (`2px × 16px` en `--faint`), etiqueta mono, cifra serif grande, subtexto muted.
- **Checkbox**: cuadrado redondeado 20px, borde `--faint`; marcado = relleno `--accent-deep` con check blanco, título tachado en `--muted`.
- **Chips de día (Gym)**: scroll horizontal, mono pequeño arriba + nombre; activo = fondo `--text` texto `--bg`.
- **Inputs numéricos (Gym)**: `--surface-2`, mono, centrados, ≥44px de alto; focus = borde `--accent`.
- **Botón primario**: `--accent-deep`, texto blanco; secundario: borde `--line` sobre transparente.
- **Nav inferior**: fija, blur, hairline superior; ítem activo en `--accent`.

## Layout

Móvil primero, columna única `max-width: 520px` centrada. Secciones encabezadas por etiqueta mono uppercase (patrón del dashboard: "TAREAS PRIORITARIAS DE HOY"). Espaciado base 4px; tarjetas separadas 10–12px.

## Motion

150–250ms, ease-out. Solo estado: aparición de pantalla (fade 6px), flare de récord, toast. `prefers-reduced-motion: reduce` desactiva todo.
