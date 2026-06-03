---
created: 2026-06-03T01:23:06.218Z
title: Utilizar el mismo modelo de inferencia de BI AI Analyst para el resumen de contexto
area: ui
files:
  - ai-analyst/app/main.py
  - ai-analyst/app/agent.py
---

## Problem

En la implementación actual de `_summarize_session()` (phase 51-03), el modelo de LLM utilizado para resumir el historial de sesión está hardcodeado o usa el default del SDK. Debería usar el mismo modelo configurado para el BI AI Analyst (el que selecciona el usuario en la interfaz — p.ej. Gemini, DeepSeek, Claude), para que el resumen sea consistente con el agente que está respondiendo y evitar llamadas a un modelo diferente sin que el usuario lo sepa.

## Solution

En `ai-analyst/app/main.py`, la función `_summarize_session()` debe leer el modelo activo del agente (el mismo que se pasa como parámetro en la request o está configurado en `agent.py`) y usarlo para la llamada de summarización en lugar de hardcodear un modelo. Si el modelo activo no soporta llamadas directas (p.ej. es solo accesible vía ADK), usar el modelo de fallback configurado. El modelo se recibe en el endpoint `/bff/ai/chat` como campo del body o header — pasarlo hasta `_summarize_session()` como argumento.
