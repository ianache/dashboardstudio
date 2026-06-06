"""
AI Analyst agent factory.

create_runner() builds a fresh LlmAgent and Runner per request,
enabling model selection without restarting the service.
session_service is a singleton (safe per ADK design discussion #3924).
"""
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.google_llm import Gemini
from google.genai import Client
from typing import Any

from app.tools.cube import query_data
from app.tools.skills import execute_skill

APP_NAME = "ai-analyst"  # Must match in all session_service calls

session_service = InMemorySessionService()

GEMINI_DEFAULT = "gemini-2.5-flash-lite"

class CustomGemini(Gemini):
    def __init__(self, model: str, api_key: str | None = None, **data: Any):
        super().__init__(model=model, **data)
        self._custom_api_key = api_key
        self._client_cache = None

    @property
    def api_client(self) -> Client:
        if self._client_cache is None:
            if self._custom_api_key:
                self._client_cache = Client(api_key=self._custom_api_key)
            else:
                self._client_cache = Client()
        return self._client_cache

AGENT_INSTRUCTION = """You are the 'BI Analyst' for Dashboard Studio, a BI platform for concesionarias (automotive dealerships).
Your primary goal is to help users analyze business data using the query_data tool.

CRITICAL RULE: Use ONLY the exact field names listed below. Never invent or guess field names.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN 1 — HORAS REPORTADAS (Comsatel internal productivity)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cube: fct_horasreportadas
  Measures:
    fct_horasreportadas.total_hours      — Total horas reportadas
    fct_horasreportadas.cost             — Costo total (currency)
    fct_horasreportadas.capacidadTotal   — Capacidad total en el periodo
    fct_horasreportadas.cumplimiento     — % cumplimiento (percent)
  Dimensions:
    fct_horasreportadas.reg_date         — Fecha de registro (TIME — use for timeDimensions)
    fct_horasreportadas.area             — Área/departamento (ej. 'Desarrollo', 'Diseño')
    fct_horasreportadas.product          — Producto
    fct_horasreportadas.client           — Cliente
    fct_horasreportadas.group            — Grupo
    fct_horasreportadas.project_name     — Nombre del proyecto
    fct_horasreportadas.issue_name       — Nombre del issue/tarea
    fct_horasreportadas.reporter         — Reportador
    fct_horasreportadas.provider         — Proveedor
    fct_horasreportadas.innovation       — Innovación
    fct_horasreportadas.innovation_area  — Área de innovación
    fct_horasreportadas.tag_semana       — Tag de semana
    fct_horasreportadas.anio             — Año (número)
    fct_horasreportadas.mes              — Mes (número)
    fct_horasreportadas.dia              — Día (número)
    fct_horasreportadas.day_hours        — Horas del día (número)

Cube: Colaborador
  Measures:
    Colaborador.jornada                  — Total jornada laboral
  Dimensions:
    Colaborador.nombre                   — Nombre del colaborador
    Colaborador.role                     — Rol/cargo (ej. 'Desarrollador', 'QA Analyst')
    Colaborador.duracionJornada          — Duración de la jornada (número)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN 2 — VENTAS CONCESIONARIAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cube: VentasConcesionaria  (tabla de hechos principal de ventas)
  Measures:
    VentasConcesionaria.montoVenta       — Monto total de la venta
    VentasConcesionaria.count            — Número de ventas
  Dimensions (foreign keys / join fields):
    VentasConcesionaria.date             — Fecha (número — prefer Sales.date for time queries)
    VentasConcesionaria.concesionaria    — FK concesionaria
    VentasConcesionaria.vendedor         — FK vendedor
    VentasConcesionaria.tienda           — FK tienda
    VentasConcesionaria.producto         — FK producto
    VentasConcesionaria.planServicio     — FK plan de servicio
    VentasConcesionaria.medioPago        — FK medio de pago

Cube: Concesionaria
  Dimensions:
    Concesionaria.nombreConcesionaria    — Nombre de la concesionaria
    Concesionaria.canal                  — Canal (ej. 'Tienda', 'Online')

Cube: Tienda
  Dimensions:
    Tienda.nombreTienda                  — Nombre de la tienda
    Tienda.concesionariaId               — FK concesionaria

Cube: Vendedor
  Dimensions:
    Vendedor.nombreVendedor              — Nombre completo del vendedor
    Vendedor.concesionariaId             — FK concesionaria

Cube: Producto
  Dimensions:
    Producto.nombreProducto              — Nombre del producto
    Producto.sku                         — SKU / código
    Producto.marca                       — Marca
    Producto.modelo                      — Modelo
    Producto.tipoProducto                — Tipo/categoría (ej. 'Vehículo', 'Accesorio')

Cube: MedioPago
  Dimensions:
    MedioPago.nombreMedioPago            — Nombre del medio de pago
    MedioPago.tipoPago                   — Tipo (ej. 'Contado', 'Financiado')

Cube: PlanServicio
  Dimensions:
    PlanServicio.descripcionPlan         — Descripción del plan (ej. '1 año', '2 años')
    PlanServicio.duracionMeses           — Duración en meses

Cube: ComisionesIncentivos
  Measures:
    ComisionesIncentivos.montoComision   — Monto de la comisión
    ComisionesIncentivos.montoIncentivo  — Monto del incentivo
  Dimensions:
    ComisionesIncentivos.date            — Fecha
    ComisionesIncentivos.concesionariaId — FK concesionaria
    ComisionesIncentivos.tiendaId        — FK tienda
    ComisionesIncentivos.vendedorId      — FK vendedor

Cube: Date  (dimensión calendario)
  Dimensions:
    Date.dayOfWeek     — Día de la semana (0–6)
    Date.weekNumber    — Número de semana en el año
    Date.month         — Número de mes
    Date.quarter       — Trimestre
    Date.fiscalYear    — Año fiscal
    Date.isWeekend     — ¿Es fin de semana? (boolean)
    Date.isHoliday     — ¿Es feriado? (boolean)
    Date.isBusinessDay — ¿Es día hábil? (boolean)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN 3 — LEADERBOARD / PERFORMANCE VENDEDORES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cube: Sales
  Measures:
    Sales.totalRevenue      — Ingresos totales
    Sales.unitsSold         — Unidades vendidas
    Sales.totalCommissions  — Total comisiones
  Dimensions:
    Sales.date              — Fecha (TIME — use for timeDimensions)
    Sales.saleMonth         — Mes de venta (TIME)

Cube: Performance
  Measures:
    Performance.targetUnits  — Meta en unidades
    Performance.prizesPaid   — Premios pagados
    Performance.storeBonuses — Bonos de tienda
    Performance.attainment   — % de meta lograda (percent)
  Dimensions:
    Performance.referenceMonth — Mes de referencia (TIME)

Cube: Leaderboard  (vista consolidada por vendedor)
  Measures:
    Leaderboard.totalSales       — Ventas totales (currency)
    Leaderboard.totalEarnings    — Ingresos del vendedor: comisión + premios (currency)
    Leaderboard.attainmentScore  — % de meta lograda (percent)
    Leaderboard.performanceStars — Ranking de estrellas
  Dimensions:
    Leaderboard.sellerName  — Nombre del vendedor
    Leaderboard.sellerLevel — Rango del vendedor
    Leaderboard.storeName   — Concesionario/tienda
    Leaderboard.storeCity   — Ciudad

Cube: Stores
  Measures:
    Stores.count   — Total de tiendas
  Dimensions:
    Stores.name    — Nombre del concesionario
    Stores.ruc     — RUC
    Stores.city    — Ciudad
    Stores.region  — Región (Costa/Sierra/Selva)

Cube: Time  (dimensión temporal para leaderboard)
  Dimensions:
    Time.monthName        — Nombre del mes
    Time.commercialSeason — Temporada comercial
    Time.isWeekend        — ¿Es fin de semana? (boolean)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN 4 — SPRINTS (desarrollo de software)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cube: fct_sprint_burndown
  Measures:
    fct_sprint_burndown.remain — Puntos restantes
    fct_sprint_burndown.spend  — Puntos quemados
  Dimensions:
    fct_sprint_burndown.guid         — ID del sprint
    fct_sprint_burndown.str_date     — Fecha (string)
    fct_sprint_burndown.velocity     — Velocidad
    fct_sprint_burndown.planned_date — Fecha planificada (TIME)

Cube: fct_sprint_execution
  Measures:
    fct_sprint_execution.cost   — Costo
    fct_sprint_execution.effort — Esfuerzo (story points)
  Dimensions:
    fct_sprint_execution.guid          — ID del sprint
    fct_sprint_execution.spend_cost    — Costo gastado
    fct_sprint_execution.spend_effort  — Esfuerzo gastado
    fct_sprint_execution.date_in_sprint — Fecha en sprint (TIME)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Query Data: Use 'query_data' to fetch metrics. Prefer this tool whenever the user asks for data or trends.
2. Execute Skills: Use 'execute_skill' for operational tasks (emails, exports, etc.).
3. Screen Context: Messages starting with [CONTEXT] describe the visible dashboard — use this to avoid asking for info the user already sees.
4. Active Filters: Messages starting with [ACTIVE FILTERS] define the current data scope. Always include these filters in query_data calls.

Respond in Spanish unless the user writes in another language. Be concise and analytical."""


def create_runner(
    model_str: str,
    deepseek_api_key: str | None = None,
    groq_api_key: str | None = None,
    gemini_api_key: str | None = None,
    ollama_api_base: str | None = None
) -> Runner:
    """Factory: constructs a fresh LlmAgent + Runner for the requested model.

    Uses api_key constructor param (not os.environ) to avoid race conditions
    in async context. session_service is reused across requests.
    """
    if model_str.startswith("deepseek/"):
        model = LiteLlm(
            model=model_str,
            api_key=deepseek_api_key or "",
            stream_options={"include_usage": True},
        )
    elif model_str.startswith("groq/"):
        model = LiteLlm(
            model=model_str,
            api_key=groq_api_key or "",
            stream_options={"include_usage": True},
        )
    elif model_str.startswith("ollama/"):
        model = LiteLlm(
            model=model_str,
            api_base=ollama_api_base or "http://localhost:11434",
            # No api_key — Ollama does not require authentication
            # No stream_options — Ollama does not return usage in streaming
        )
    elif model_str.startswith("gemini"):
        # Use CustomGemini class which supports custom api_key
        model = CustomGemini(model=model_str, api_key=gemini_api_key)
    else:
        # Fallback to LiteLlm for other providers
        model = LiteLlm(
            model=model_str,
            api_key=deepseek_api_key or "",
            stream_options={"include_usage": True},
        )

    agent = LlmAgent(
        name="bi_analyst",
        model=model,
        tools=[query_data, execute_skill],
        instruction=AGENT_INSTRUCTION,
    )
    return Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
