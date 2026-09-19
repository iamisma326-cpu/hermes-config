# Local LLM fit para esta máquina (investigación 2026-09-13)

Investigación en tiempo real (Hugging Face API + pacman + lscpu). Instalación NO ejecutada aún — pedir visto bueno antes de instalar.

## Hardware medido ese día
- CPU: AMD Ryzen 3 3200G — 4c/4t, 3.7-4.0 GHz, AVX2 OK (flag verificado en lscpu)
- RAM: 7.4 GB total; en uso ~6.4-6.7 GB + zram 7.4G parcialmente lleno → ~1 GB libre real
- GPU: SOLO iGPU Vega 11 (Picasso/Raven, PCI 30:00.0). Sin NVIDIA/ROCm. Vulkan ICD presente (vulkan-radeon) pero sin VRAM dedicada — offload iGPU no aporta mucho
- Disco: 85G con 9.3G libres (90%) → un modelo a la vez, ≤ ~3 GB
- OS: CachyOS; repos traen llama-cpp 0.4.0 y ollama 0.34.0 (`pacman -S llama-cpp`)

## Recomendación
- Principal: unsloth/Qwen3.5-4B-GGUF → Q4_K_M = 2613.96 MB (2.6 GB). Trending #1 en apps=llama.cpp. Chat + razonamiento + código ligero.
- Plan B con más margen de RAM: LiquidAI/LFM2.5-2.6B → Q4_K_M = 1596.88 MB (1.6 GB). Muy rápido en CPU.
- Variante: empero-ai/Qwen3.8-4B-Distill → Q4_K_M = 2654.5 MB.
- Máximo aceptable: Qwen3.5-4B Q6_K = 3362.61 MB (apretado con navegador abierto).

Quants verificados por tree API (unsloth/Qwen3.5-4B-GGUF): IQ4_NL 2460 MB, Q3_K_M 2187 MB, Q5_K_M 2998 MB, Q6_K 3362 MB, Q8_0 4275 MB, UD-Q4_K_XL 2777 MB. (mmproj-*.gguf = proyector multimodal, NO es el modelo.)

## Plan de conexión a Hermes (no ejecutado)
1. sudo pacman -S llama-cpp
2. llama-server -hf unsloth/Qwen3.5-4B-GGUF:Q4_K_M --host 127.0.0.1 --port 8080 -c 8192 -t 4
3. hermes config set model.provider custom ; hermes config set model.base_url http://127.0.0.1:8080/v1 ; hermes config set model.api_key local
   (o alias: model.aliases.local-qwen → provider custom, base_url arriba, para cambiar con /model local-qwen)
4. Expectativa: ~5-12 tok/s en esta CPU; cerrar navegador pesado antes (con 1 GB libre no cabe sin swap).

## Quirks de APIs (lecciones de la investigación)
- HF models API: sort=trending da 400 ("Invalid sort parameter") — usar sort=downloads&direction=-1.
- HF tree API (tamaños exactos de GGUF): https://huggingface.co/api/models/<repo>/tree/main → filtrar .gguf, size/1048576. `?recursive=true` para subdirectorios.
- Nombre de paquete en pacman: llama-cpp (NO "llama.cpp"); ollama normal/cuda/rocm/vulkan como variantes.
- curl UA custom (curl/8.0) funcionó con HF; jq disponible en el sistema.

## Decisión vigente
El usuario sigue con glm-5.3-free por TokenRouter (default fijado 2026-09-13). El modelo local queda como opción evaluada, no instalada.
