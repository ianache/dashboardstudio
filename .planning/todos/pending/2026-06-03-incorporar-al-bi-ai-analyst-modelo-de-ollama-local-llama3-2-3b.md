---
created: 2026-06-03T02:13:14.410Z
title: Incorporar al BI AI Analyst modelo de Ollama local llama3.2:3b
area: ui
files:
  - ai-analyst/app/agent.py
  - ai-analyst/app/main.py
  - dashboard-app/src/components/dashboard/AiAnalystPanel.vue
---

## Problem

El BI AI Analyst actualmente soporta Gemini (vía Google GenAI SDK) y DeepSeek/Groq (vía LiteLLM). No hay soporte para modelos locales servidos por Ollama, que es el runtime más común para ejecutar LLMs en máquinas locales sin depender de APIs externas ni incurrir en costos por token. El modelo llama3.2:3b es especialmente útil para desarrollo y pruebas offline: es pequeño (~2 GB), rápido en CPU/GPU modestas, y suficientemente capaz para análisis BI básico.

## Solution

Ollama expone una API compatible con OpenAI en `http://localhost:11434/v1`, por lo que se puede integrar via `LiteLlm` del ADK usando el prefix `ollama/` (que LiteLLM ya soporta nativamente).

**Backend (`ai-analyst/app/agent.py`):**
```python
elif model_str.startswith("ollama/"):
    model = LiteLlm(
        model=model_str,           # e.g. "ollama/llama3.2:3b"
        api_base="http://localhost:11434",
    )
```
No se necesita `api_key` — Ollama no requiere autenticación por defecto.

**Backend (`ai-analyst/app/main.py`):**
- Agregar el modelo a la lista de `/models` endpoint, posiblemente con `enabled: False` por defecto (ya que Ollama debe estar corriendo localmente). Puede tener un health-check previo: `GET http://localhost:11434/api/tags` y verificar que `llama3.2:3b` esté en la lista antes de marcarlo como `enabled: True`.
- Para `_summarize_session()`: si el modelo activo es `ollama/*`, usar `FALLBACK_SUMMARY_MODEL` (ya que la llamada directa a genai no aplica).

**Frontend (`AiAnalystPanel.vue`):**
- El selector de modelos ya se alimenta del endpoint `/models`, así que el modelo aparecerá automáticamente si el backend lo incluye en la respuesta.
- Considerar mostrar un badge "Local" o "Offline" para distinguirlo de los modelos cloud.

**Consideraciones:**
- Ollama debe estar corriendo en localhost:11434 en la máquina donde corre `ai-analyst`. En Docker, necesitaría `host.docker.internal:11434`.
- El modelo `llama3.2:3b` debe estar descargado: `ollama pull llama3.2:3b`.
- Streaming: LiteLLM con Ollama soporta streaming igual que con otros providers, no se requieren cambios en el loop de SSE.
