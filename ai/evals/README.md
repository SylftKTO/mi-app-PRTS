# PRTS · Evals de prompts (§10.7)

Casos de regresión `entrada → salida esperada` para los prompts versionados.
**Antes de subir un `prompt.vN+1`, corre el set y compara aciertos con vN.**

```
inbox.cases.jsonl     # capturas → {module, action, payload parcial}
command.cases.jsonl   # comandos → {intent, params parcial}
run.ts                # runner (Deno, usa el mismo llm.ts y schemas.ts de producción)
```

## Correr

```powershell
$env:LLM_API_KEY = "sk-..."
deno run --allow-net --allow-env --allow-read ai/evals/run.ts inbox
deno run --allow-net --allow-env --allow-read ai/evals/run.ts command
```

La comparación es **parcial**: cada campo declarado en `expect` debe coincidir
en la salida del modelo; los campos no declarados se ignoran.

## Flujo al cambiar un prompt

1. Crea `prompts/<agente>.vN+1.ts` (conserva el vN).
2. Cambia el import en `run.ts` al vN+1 y corre el set → anota aciertos.
3. Si mejora o iguala, apunta la Edge Function al vN+1 y despliega.
4. Si algo del uso real falla, agrega el caso aquí (así el set crece con datos reales).

Cada corrida cuesta ~17 llamadas al tier económico (centavos), y NO se registra
en `ai_calls` (corre fuera de las Edge Functions).
