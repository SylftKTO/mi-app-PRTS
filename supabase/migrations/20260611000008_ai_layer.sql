supabase secrets set LLM_API_KEY=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
supabase secrets set LLM_MODEL=claude-haiku-4-5-20251001   
supabase secrets set LLM_PRICE_IN=1        
supabase secrets set LLM_PRICE_OUT=5       
supabase functions deploy generate-briefing









supabase secrets set LLM_API_KEY=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
supabase secrets set LLM_MODEL=claude-haiku-4-5-20251001
supabase secrets set LLM_PRICE_IN=... LLM_PRICE_OUT=...   # tarifas vigentes (para el costo)
supabase functions deploy generate-briefing
# probar:
#   curl -X POST .../functions/v1/generate-briefing -H "Authorization: Bearer <SERVICE_ROLE_KEY>" -d '{"force":true}'
# programar (10:30 MX = 16:30 UTC) con pg_cron — ver supabase/functions/README.md
git add -A && git commit -m "Fase 4.0: capa IA (backend, briefing diario, logging de costos)" && git push