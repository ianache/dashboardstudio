# Phase 52: LLM Completion — Interpolación de variables ctx - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Habilitar interpolación de variables Jinja2 en los campos `user_prompt` y `system_prompt` del nodo **LLM Completion** en Integration Flows.

- `user_prompt` ya renderiza Jinja2 en el backend (llm_executor.py) — solo falta el hint en el UI
- `system_prompt` no renderiza nada actualmente — agregar rendering Jinja2 en llm_executor.py
- Mostrar hints visuales en ambos campos (mismo estilo `.fec-template-hint` que Email)

Fuera de alcance: cambios en otros tipos de nodo, nuevos filtros Jinja2, preview de templates.

</domain>

<decisions>
## Implementation Decisions

### Variables disponibles en ctx
- Contexto expuesto: `{ payload, variables }` — mismo que usa `user_prompt` actualmente
- `{{ payload }}` para el array/objeto completo de entrada al nodo
- `{{ payload[0].campo }}` para acceder a un campo del primer registro
- `{{ variables.nombre }}` para las variables del flow
- NO se agregan aliases ni conveniencias adicionales — Jinja2 nativo tiene |tojson si se necesita

### Comportamiento ante errores de template
- **Errores de sintaxis** (template inválido): fallar el nodo con mensaje de error claro — igual al comportamiento actual de user_prompt
- **Variables inexistentes** (ej: `{{ payload.campoQueNoExiste }}`): silencio — renderizar como string vacío (comportamiento default de Jinja2, NO activar StrictUndefined)

### Hints en el UI (FlowEditorCanvas.vue)
- Un hint debajo de cada textarea: uno bajo `user_prompt` y otro bajo `system_prompt`
- Mismo componente CSS `.fec-template-hint` que ya usa el nodo Email
- Texto idéntico en ambos campos, mostrando variables disponibles explícitamente:
  `Usa {{ payload.campo }} y {{ variables.nombre }}. Soporta filtros Jinja2 como | tojson`
- Condición del v-if: cuando el toolType del nodo sea `llm` Y el key sea `user_prompt` o `system_prompt`

### Alcance por campo
- `user_prompt`: SOLO agregar hint en UI (backend ya funciona correctamente — no tocar)
- `system_prompt`: agregar rendering Jinja2 en `llm_executor.py` (misma capa que user_prompt) + hint en UI
- El rendering ocurre en Python (`llm_executor.py`), NO en Deno runner — el nodo LLM es pre-ejecutado por Python

### Claude's Discretion
- Orden exacto del rendering en llm_executor.py (renderizar system_prompt antes o después de user_prompt — ambos con el mismo ctx)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `jinja2.Template().render()`: ya usado en llm_executor.py para user_prompt — clonar el mismo patrón para system_prompt
- `.fec-template-hint` CSS class: ya definida en FlowEditorCanvas.vue (líneas 2838-2855) — reusar directamente
- `resolveTemplates()` en runner.ts: función Nunjucks para Email/HTTP — NO usarla para LLM (diferente motor, diferente capa)

### Established Patterns
- Email node hint check: `v-if="key === 'subject'"` y `v-if="def.type === 'textarea' && ['subject', 'body'].includes(key)"` — mismo patrón aplicar para `['user_prompt', 'system_prompt'].includes(key)` con `selectedNode.toolType === 'llm'`
- user_prompt Jinja2 context en llm_executor.py: `ctx if isinstance(ctx, dict) and "payload" in ctx else {"payload": ctx, "data": ctx, "variables": {}}`
- system_prompt actualmente: `system_prompt = props.get("system_prompt") or "You are a helpful assistant."` — agregar rendering después de obtener el valor

### Integration Points
- `backend/app/services/llm_executor.py` — agregar 1 bloque try/except de Jinja2 para system_prompt (igual al de user_prompt)
- `dashboard-app/src/components/editor/FlowEditorCanvas.vue` — agregar 1 `<p v-if>` para LLM fields (líneas ~716-723, junto a los hints de Email)

</code_context>

<specifics>
## Specific Ideas

- El usuario mencionó explícitamente `ctx` como la fuente de variables — el hint debe nombrar `payload` y `variables` ya que son las claves reales del contexto
- La paridad con Email (nodo similar en notificaciones) es la referencia de diseño — mismo estilo visual, mismo patrón de hints

</specifics>

<deferred>
## Deferred Ideas

- None — la discusión se mantuvo dentro del alcance de la fase

</deferred>

---

*Phase: 52-mejorar-nodo-llm-completion*
*Context gathered: 2026-06-05*
