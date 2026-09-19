---
name: hermes-model-ops
description: "Use when changing or fixing Hermes Agent's default model."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, model, provider, config, llama.cpp, local-llm]
    related_skills: [hermes-agent, llama-cpp]
---

# Hermes Model & Provider Ops

Fijar, cambiar o diagnosticar el modelo con el que Hermes Agent arranca por defecto, y evaluar modelos locales (llama.cpp) para esta máquina.

## When to Use (Cuándo usar)
- "haz que X sea el modelo por defecto en hermes" / "que hermes inicie con X"
- "al iniciar sesión nueva no aparece el modelo X" (arranca con otro)
- Cambiar de proveedor, o conectar/evaluar un modelo local como provider custom

## Procedimiento verificado (2026-09-13, Hermes v0.20.5)

1. LEER el estado actual — siempre primero, también si el usuario reporta que algo "se rompió":
   hermes config get model

2. Localizar el proveedor. DOS ubicaciones posibles:
   a) Sección `providers:` en ~/.hermes/config.yaml (base_url, key_env, default_model)
   b) Plugins Python: ~/.hermes/plugins/model-providers/<nombre>/__init__.py
      (ProviderProfile: name, env_vars, base_url — tokenrouter está definido así, NO en config.yaml)
   Que grep en config.yaml no encuentre el proveedor NO significa que no exista: revisa el directorio de plugins.
   Inventario rápido:
   grep -A4 'providers:' ~/.hermes/config.yaml ; ls ~/.hermes/plugins/model-providers/

3. Verificar el ID EXACTO del modelo EN VIVO (obligatorio: los routers agregadores usan prefijo de vendor — z-ai/glm-5.3-free, NO glm-5.3-free):
   KEY=$(grep '^<KEY_ENV>=' ~/.hermes/.env | cut -d= -f2)
   curl -s <base_url>/models -H "Authorization: Bearer $KEY" | jq -r '.data[].id' | grep -i <nombre>

4. Fijar el default. NUNCA editar config.yaml a mano (un indent malo rompe el gateway en vivo):
   hermes config set model.provider <proveedor>
   hermes config set model.default <id-exacto-del-paso-3>

5. Verificar el resultado:
   hermes config get model   → debe mostrar default + provider nuevos

Ejemplo real verificado (tokenrouter → glm-5.3-free):
   hermes config set model.provider tokenrouter
   hermes config set model.default z-ai/glm-5.3-free
   # provider plugin: base_url https://api.tokenrouter.com/v1, key_env TOKENROUTER_API_KEY

## Pitfalls
- Turno interrumpido ≠ cambio aplicado. Ante "ya no aparece X / creo que lo rompiste" tras una sesión interrumpida: correr el paso 1 y mostrar el estado real ANTES de cualquier explicación (2026-09-13: la interrupción llegó antes del paso 4; no se había escrito nada — el síntoma era que el cambio nunca se aplicó).
- Un ID mal escrito no falla ruidosamente: produce fallback silencioso a otro modelo. El paso 3 no es opcional.
- 403 con `error code: 1010` (Cloudflare) al consultar /models con UA de Python/curl NO significa provider muerto — varios routers (apinex, xkiro, freemodel, kktoken, vyce, codecraft) lo bloquean. Reintentar con UA de navegador (`curl -A 'Mozilla/5.0 ...'`): verificado 2026-09-18, los 403 se vuelven 200. Concluir "muerto" solo tras probar ambos UAs y un chat real.
- Los `fallback_models` de los plugins (~/.hermes/plugins/model-providers/*/__init__.py) caducan igual que los defaults — verificarlos también contra la lista en vivo (2026-09-18: apinex tenía 9 IDs muertos, formato cambió de vendor/model a plano; xkiro y modelscope 1 c/u).
- Verificar que un router sirve el modelo ETIQUETADO (no solo que el ID exista): fingerprint de tokenizer. Misma cadena a 2+ endpoints → comparar prompt_tokens: deltas (B−A, C−A, D−A) con 3-4 cadenas distintos idénticos = mismo modelo; offset constante = solo chat template distinto; deltas distintos = modelo distinto. Caso real 2026-09-18: nvidia z-ai/glm-5.3 ≡ dahl zai-org/GLM-5.3-Flash (B=52/C=43/D=44 exacto) = genuinos; unorouter glm-5.3*:free da deltas distintos y self-ID "GLM-5.2" → sirve GLM-5.2 bajo etiqueta 5.3.
- `/model <x>` dentro de una sesión es scoped a ESA sesión. Si el usuario quiere que persista al INICIAR hermes: model.provider + model.default (paso 4). (`/model <x> --global` también persiste; config set es el mecanismo directo y verificable.)
- Las keys viven en ~/.hermes/.env (nombre = key_env del provider en config.yaml, o env_vars del plugin).
- Provider en config.yaml pero /model el picker sale VACÍO: el picker NO consulta la lista del endpoint /models por sí solo; exige un ProviderProfile registrado como plugin. `hermes config set providers.X.{type,base_url,key_env}` registra las credenciales, sin más. El modelo elegible cae al path genérico `provider_model_ids(normalized)` en hermes_cli/models.py:4100+, que requiere `get_provider_profile(normalized)` definido. Fixes: 1) crear ~/.hermes/plugins/model-providers/<name>/{__init__.py,plugin.yaml} con ProviderProfile(name, env_vars, base_url, fallback_models) y register_provider(); 2) si hay que filtrar la lista live (ej: solo free), hacer subclass de ProviderProfile y override fetch_models() (ver template en references/provider-plugin-zenmux.md). Verificado 2026-09-16: tras crear el plugin + reload, `provider_model_ids('zenmux')` devuelve los IDs correctos en vivo.

## Añadir provider custom desde cero (con picker poblado)
Secuencia completa mínima que deja el picker funcionando (verificada 2026-09-16, Hermes v0.20.5):

1. Config en `~/.hermes/config.yaml` vía hermes CLI:
   hermes config set providers.<slug>.type openai
   hermes config set providers.<slug>.base_url <base-url>
   hermes config set providers.<slug>.key_env <ENV_VAR>
2. Key en `~/.hermes/.env`: `<ENV_VAR>=<api-key>`
3. Plugin en `~/.hermes/plugins/model-providers/<slug>/__init__.py` llamando `register_provider(ProviderProfile(name=<slug>, env_vars=(<ENV_VAR>,), base_url=<base-url>, fallback_models=(...)))`. Compañero `plugin.yaml` con `kind: model-provider`.
4. Si hay filtrado (sólo free, sólo chat, etc.) → subclass ProviderProfile con fetch_models custom. La base clase ya sabe hablar OpenAI-compat; personalizar el parseo de `data` y devolver lista de IDs.
5. Recargar el picker (`/model --refresh` o reabrir hermes). Sin caché persistente en disco para resultados vacíos (TTL 1h solo para éxitos), así que un pick vacío previo no bloquea.

## Referencias
- references/local-model-fit.md — hardware real (Ryzen 3200G, 7.4GB, solo iGPU, disco 90%), GGUFs con tamaños verificados, quirks de la API de Hugging Face.
- references/provider-plugin-zenmux.md — ejemplo verificado de ProviderProfile con fetch_models custom que filtra /models por pricing==0 (caso zenmux: 7 modelos free). Reusable para cualquier router que publique `pricings` en su /models.

## Modelo local para esta máquina
Elección recomendada, tamaños exactos de GGUF y plan de conexión: `references/local-model-fit.md`
(investigación 2026-09-13; instalación NO ejecutada aún — pedir visto bueno antes de instalar).

## Referencias
- references/local-model-fit.md — hardware real (Ryzen 3200G, 7.4GB, solo iGPU, disco 90%), GGUFs con tamaños verificados, quirks de la API de Hugging Face.
