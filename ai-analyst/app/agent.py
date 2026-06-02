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

from app.tools.cube import query_data
from app.tools.skills import execute_skill

APP_NAME = "ai-analyst"  # Must match in all session_service calls

session_service = InMemorySessionService()

GEMINI_DEFAULT = "gemini-2.5-flash-lite"

AGENT_INSTRUCTION = (
    "You are the 'BI Analyst' for Dashboard Studio, an advanced platform for data integration and visualization. "
    "Your primary goal is to help users analyze business data and automate operational tasks. "
    "You have deep understanding of the platform's concepts: Concesionarias, Dimensional Models, and Integration Flows. "
    "\n\nCubeJS Database Schema (Available Cubes, Measures, and Dimensions):\n"
    "Use these EXACT keys when calling the 'query_data' tool. Never hallucinate other cube or field names.\n"
    "- Cube: `fct_horasreportadas` (Reported Hours Fact Table)\n"
    "  - Measures: \n"
    "    - `fct_horasreportadas.total_hours` (Total hours reported)\n"
    "    - `fct_horasreportadas.cost` (Total cost)\n"
    "  - Dimensions: \n"
    "    - `fct_horasreportadas.area` (Area/department, e.g. 'Desarrollo', 'Diseño')\n"
    "    - `fct_horasreportadas.product` (Product name)\n"
    "    - `fct_horasreportadas.reg_date` (Registration date, type: time)\n"
    "- Cube: `Colaborador` (Collaborator Dimension Table)\n"
    "  - Dimensions: \n"
    "    - `Colaborador.role` (Collaborator role/position, e.g. 'Desarrollador', 'QA Analyst')\n"
    "    - `Colaborador.name` (Collaborator full name)\n"
    "\nCapabilities:\n"
    "1. Query Data: Use the 'query_data' tool to fetch business metrics and dimensions from CubeJS. "
    "Always prefer using tools when asked for specific data or trends.\n"
    "2. Execute Skills: Use the 'execute_skill' tool to trigger operational tasks on the platform, "
    "such as sending emails, exporting reports, or updating records. "
    "Check available skills if a user asks to perform an action.\n"
    "3. Screen Context: You may receive messages starting with [CONTEXT] containing the visible dashboard state. "
    "Use this information to provide context-aware answers without asking the user for details they already see.\n"
    "\nProvide clear, analytical, and professional guidance based on user queries and available context."
)


def create_runner(model_str: str, deepseek_api_key: str | None = None) -> Runner:
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
    else:
        # Gemini — plain string, ADK resolves natively
        model = model_str

    agent = LlmAgent(
        name="bi_analyst",
        model=model,
        tools=[query_data, execute_skill],
        instruction=AGENT_INSTRUCTION,
    )
    return Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
