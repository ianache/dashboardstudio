# PRD

## Etapa 1: Agente Analista BI Base (Enfoque Datos y Acción)
**Objetivo:** Desplegar el agente inteligente interactivo capaz de leer la interfaz actual, ejecutar acciones operativas y consultar métricas estructuradas directamente.
### Alcance Técnico y Arquitectura
 * **Frontend (Vue 3 + Pinia):** Captura el estado actual de los datos reflejados en los componentes de gráficos (Screen Context) y maneja la interfaz de chat con el usuario.
 * **BFF (Node.js):** Valida las sesiones de usuario, gestiona la seguridad y actúa como pasarela de comunicación orientada al backend.
 * **Servicio IA (Python + Google ADK):** Orquesta el flujo analítico inicial utilizando modelos Gemini (vía API nativa).
 * **Capa de Datos y Operaciones:** * Integración con la API de **Cube.js** para consultas analíticas directas basadas en dimensiones y medidas explícitas.
   * Integración con el repositorio **skills-catalog** leyendo dinámicamente el archivo catalog.yaml para habilitar acciones operativas específicas bajo demanda del usuario.
### Capacidades del Agente en esta Etapa
 * **Interpretación descriptiva:** Explicar tendencias, picos o caídas visibles en los gráficos actuales del dashboard.
 * **Consultas ad-hoc:** Ejecutar consultas estructuradas adicionales a Cube.js si el usuario pide profundizar en un dato que no está mapeado en la pantalla.
 * **Automatización de tareas:** Disparar habilidades (*skills*) técnicas o de negocio preconfiguradas en el catálogo operativo.
## Etapa 2: Agente Analista BI Avanzado (Enfoque Semántico y de Negocio)
**Objetivo:** Dotar al agente de un marco cognitivo superior, permitiéndole entender "el significado" y las reglas interconectadas de las métricas de la empresa a través de ontologías.
### Alcance Técnico y Arquitectura
 * **Mantenimiento de la Infraestructura Base:** Se conservan intactos los flujos de Vue, Pinia, el BFF y el catálogo de habilidades de la Etapa 1.
 * **Integración de kmportal (Capa de Conocimiento):** Se introduce el motor de ontologías y el grafo de conocimiento del portal dentro del servicio de Google ADK en Python.
 * **Ampliación del Tooling:** Se activa la herramienta de mapeo de conceptos semánticos (get_ontology_mapping) para que el agente consulte el contexto de las reglas del negocio antes de responder.
### Capacidades del Agente en esta Etapa
 * **Razonamiento Conceptual Extendido:** El agente ya no solo ve números o etiquetas aisladas; entiende la jerarquía del negocio. Si analiza el *Margen Neto*, sabrá de forma autónoma qué variables del negocio lo impactan según la ontología de kmportal.
 * **Validación de Reglas de Negocio Complejas:** Capacidad para cruzar axiomas, restricciones y dependencias semánticas del negocio (ej. *"Esta métrica de inventario está en alerta porque la regla ontológica X indica que la fase pre-operativa requiere un stock triple"*).
 * **Análisis Causa-Raíz Automatizado:** Al entender el grafo de relaciones de la empresa, el agente puede saltar de una anomalía en un gráfico a investigar causas en conceptos del negocio que ni siquiera se muestran en el dashboard actual del usuario.

# Referencias Adicionales
Estas referencias adicionales las usaremos en la Etapa 2:

- KM Portal (Ontologias): Tengo un repositorio https://github.com/ianache/kmportal con una plataforma para KM basada en Ontologias.
- Skill Catalog: tengo un repositorio que contiene catalogo de skills (https://github.com/ianache/skills-catalog) y expone un archivo catalogo de skills preconstruidos (https://github.com/ianache/skills-catalog/blob/main/catalog.yaml) que me  gustaria tambien poder integrar a la solucion.

# UX/UI Design

- Usar el diseño del Agente AI para BI desde Google Stitch siguiente https://stitch.withgoogle.com/projects/13552735885366810005?node-id=44e7eb3446dc4996a7b7dad2a7127083