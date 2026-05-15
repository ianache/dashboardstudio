# Investigación: Motor de Ejecución de Integraciones con Deno

**Fecha:** 14 de Mayo, 2026
**Dominio:** Backend (FastAPI, Deno), Frontend (Vue 3)
**Confianza:** ALTA (Basado en documentación oficial y patrones estándar de la industria)

## Resumen Ejecutivo

Para añadir capacidad de scripting a los flujos de integración, se propone utilizar **Deno** como runtime de ejecución debido a su arquitectura segura por defecto (sandboxing) y su excelente soporte nativo para TypeScript/JavaScript. El backend FastAPI orquestará la ejecución mediante subprocesos, capturando logs en tiempo real y gestionando el aislamiento de recursos.

**Recomendación principal:** Utilizar un "Runner" central en Deno que procese el grafo del flujo, ejecutando los nodos de script en un entorno restringido, y comunicar los resultados y logs de vuelta al backend mediante tuberías (pipes) estándar y WebSockets.

---

## 1. Capacidad de Script en `IntegrationFlow`

### Propuesta de Esquema
Se extenderá la estructura de los objetos dentro de `flow_nodes` para soportar una propiedad `data.code` cuando el tipo de nodo sea `script`.

**Ejemplo de nodo en `flow_nodes`:**
```json
{
  "id": "node_123",
  "type": "script",
  "label": "Transformar Datos",
  "data": {
    "code": "export default async function(ctx) {\n  const { payload } = ctx;\n  console.log('Procesando datos...');\n  return { ...payload, processed: true };\n}",
    "inputs": [...],
    "outputs": [...]
  }
}
```

---

## 2. Ejecución en Deno (Backend FastAPI)

### Seguridad e Aislamiento
Deno es ideal para ejecutar código no confiable debido a su modelo de permisos explícitos.

*   **Flags de Seguridad:**
    *   `--no-remote`: Evita que el script descargue dependencias externas en runtime.
    *   `--allow-net` (opcional): Solo si se permiten peticiones HTTP externas (ej. Webhooks).
    *   `--v8-flags=--max-old-space-size=256`: Limita el uso de memoria RAM a 256MB.
*   **Aislamiento de Recursos (Linux):**
    *   En producción, se recomienda usar **Docker** con límites de memoria/CPU o **Cgroups v2** directamente para evitar ataques de denegación de servicio (bucles infinitos, consumo masivo de CPU).
*   **Timeouts:**
    *   El proceso de Python debe manejar un timeout estricto (ej. 30s) para terminar el subproceso si no responde.

### Integración Python -> Deno
```python
import subprocess
import asyncio

async def run_flow(flow_json: str):
    process = await asyncio.create_subprocess_exec(
        "deno", "run", 
        "--no-remote",
        "--v8-flags=--max-old-space-size=256",
        "runner.ts",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Pasar el flujo por stdin
    stdout, stderr = await process.communicate(input=flow_json.encode())
    # ... procesar resultados
```

---

## 3. Gestión de Logs en Tiempo Real

Para mostrar logs en la UI mientras el script corre:

1.  **Backend:** FastAPI utiliza un `WebSocket` que lee línea por línea el `stdout` del proceso Deno.
2.  **Deno:** Cualquier `console.log()` en el script del usuario se escribe en `stdout`.
3.  **Frontend:** Un componente de terminal (o simple lista de logs) se suscribe al WebSocket.

**Flujo de Datos:**
`Deno (console.log)` -> `Python (stdout.readline)` -> `FastAPI (WebSocket.send_text)` -> `Vue (UI)`

---

## 4. Arquitectura del Motor de Ejecución

### Orquestación de Nodos (Runner.ts)
El "Runner" es un script de Deno que:
1.  Recibe el JSON del flujo.
2.  Calcula el orden de ejecución (Topological Sort para DAG).
3.  Mantiene un objeto `context` que contiene:
    *   `payload`: Los datos actuales que fluyen por el grafo.
    *   `variables`: Estado persistente durante la ejecución del flujo.
4.  **Ejecución de Scripts:**
    Utiliza `eval()` o `new Function()` para ejecutar el string de código dentro del runner. Al estar ya dentro de un proceso Deno restringido, el riesgo está contenido.

### Paso de Datos entre Nodos
```typescript
// Estructura interna del Runner
let currentPayload = initialData;

for (const node of sortedNodes) {
  if (node.type === 'script') {
    const userFunc = new Function('ctx', node.data.code);
    currentPayload = await userFunc({ payload: currentPayload, vars });
  } else {
    currentPayload = await executeBuiltInNode(node, currentPayload);
  }
}
```

---

## 5. Librerías Frontend (Edición de Código)

Para editar el código en Vue 3, se recomiendan dos opciones según la complejidad deseada:

### Opción A: Monaco Editor (Recomendada para "Power Users")
Es el motor de VS Code. Ofrece la mejor experiencia de autocompletado y validación.
*   **Librería:** `@guolao/vue-monaco-editor`
*   **Pros:** Experiencia profesional, temas, autocompletado de tipos Deno/TS.
*   **Contras:** Bundle pesado (>5MB), requiere configuración de workers en Vite.

### Opción B: CodeMirror 6 (Recomendada por Ligereza)
*   **Librería:** `vue-codemirror`
*   **Pros:** Muy ligero, excelente soporte para móviles, arquitectura modular.
*   **Contras:** Menos "IDE-like" que Monaco por defecto.

---

## Propuesta Técnica Detallada

### Fase 1: Backend - Infraestructura Deno
*   Crear `runner.ts` base en el backend.
*   Implementar servicio `FlowExecutionService` en FastAPI que use `subprocess`.
*   Configurar Dockerfile para incluir el binario de Deno.

### Fase 2: Backend - API de Ejecución
*   Endpoint POST `/flows/{id}/run` para ejecuciones manuales.
*   Endpoint WebSocket `/flows/{id}/logs` para streaming de salida.

### Fase 3: Frontend - Editor de Nodos
*   Integrar `@guolao/vue-monaco-editor` en un modal de configuración de nodos.
*   Añadir panel de "Consola" para mostrar los logs del WebSocket.

---

## Fuentes
*   [Deno Security Manual](https://docs.deno.com/runtime/manual/basics/permissions/) - Seguridad por defecto.
*   [FastAPI Subprocesses](https://fastapi.tiangolo.com/advanced/async-tests/#asynchronous-subprocesses) - Ejecución asíncrona de comandos.
*   [V8 Flags](https://v8.dev/docs/flags) - Control de memoria y recursos.
*   [Vue-Monaco-Editor](https://github.com/imguolao/monaco-editor-vue3) - Integración con Vue 3.
