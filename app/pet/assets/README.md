# Arte del avatar de la mascota (Fase 9)

`avatar.js` **alterna el archivo según el estado**. Hoy hay placeholders **SVG** on-brand
(rosa/gris). Para el arte real (anime, coherente con PRTS-002) basta dejar los archivos
con **el mismo nombre** aquí y activar WebP — sin tocar código.

## Cómo activar el arte WebP

1. Coloca los `.webp` en esta carpeta con los nombres de la tabla.
2. En **Elfie → Elfie Core → "Avatar animado (WebP)"**, activa el toggle.
   (Internamente llama `Avatar.setExt("webp")`; persiste en `localStorage` `prts_pet_ext`.)
3. Para volver a SVG, apaga el toggle.

> El sistema arma la ruta como `pet/assets/<estado>.<ext>`. Si activas WebP y falta algún
> archivo, ese estado saldrá roto → ten los de la tabla antes de activar.

## Formato sugerido

- **Lienzo 200×200**, fondo **transparente** (alfa). Sujeto centrado, margen ~14 px.
- **WebP animado** (loop) para vida sutil; o WebP estático si no animas ese estado.
- Peso objetivo < 60 KB por archivo (son ligeros y se precargan todos).
- Paleta: rosa `#E68AA2` / rosa profundo `#B04A62` / grises del sistema; rojo `#E0626C` solo error.
- Respeta `prefers-reduced-motion`: el loop debe verse bien aunque el navegador lo congele.

## Estados requeridos

| Archivo | Estado | Notas |
|---|---|---|
| `neutral.webp` | reposo | idle: parpadeo/respiración |
| `listening.webp` | escuchando | pulso |
| `thinking.webp` | pensando | mirada/“…” |
| `speaking.webp` | hablando (boca abierta) | **par con** `speaking-closed` |
| `speaking-closed.webp` | hablando (boca cerrada) | lip-sync: alterna con `speaking` cada 150 ms |
| `error.webp` | error / no entendí | glitch breve |

### Contextuales (pose de reposo por módulo)

| Archivo | Módulo |
|---|---|
| `study.webp` | Apuntes / estudio |
| `gym.webp` | Gimnasio |
| `finance.webp` | Finanzas |
| `diet.webp` | Dieta |
| `levelup.webp` | LevelUp |
| `music.webp` | Música |

### Aliases (NO requieren archivo propio)

`executing` → usa `thinking` · `confirming` → usa `listening` · `alert` → usa `error`.
Si quieres arte propio para ellos, crea `executing.webp` / `confirming.webp` / `alert.webp`
y actualiza el mapa `ASSETS` en `app/pet/avatar.js`.

## Mínimo viable

Con los **6 base** (`neutral`, `listening`, `thinking`, `speaking`, `speaking-closed`, `error`)
ya se ve completo. Los 6 contextuales son un plus; sin ellos, el reposo usa `neutral`.
