"""
Google ADK agent singleton.

The Runner and session_service are module-level singletons — safe for concurrent
reuse per ADK design (discussion #3924). Only session_id varies per request.
"""
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.core.config import get_settings
from app.tools.cube import query_data
from app.tools.skills import execute_skill

APP_NAME = "ai-analyst"  # Must match in all session_service calls

settings = get_settings()

session_service = InMemorySessionService()

root_agent = LlmAgent(
    name="bi_analyst",  # underscores required — ADK validates Python identifier
    model=settings.gemini_model,
    tools=[query_data, execute_skill],
    instruction=(
        "You are the 'BI Analyst' for Dashboard Studio, an advanced platform for data integration and visualization. "
        "Your primary goal is to help users analyze business data and automate operational tasks. "
        "You have deep understanding of the platform's concepts: Concesionarias, Dimensional Models, and Integration Flows. "
        "\n\nCapabilities:\n"
        "1. Query Data: Use the 'query_data' tool to fetch business metrics and dimensions from CubeJS. "
        "Always prefer using tools when asked for specific data or trends.\n"
        "2. Execute Skills: Use the 'execute_skill' tool to trigger operational tasks on the platform, "
        "such as sending emails, exporting reports, or updating records. "
        "Check available skills if a user asks to perform an action.\n"
        "3. Screen Context: You may receive messages starting with [CONTEXT] containing the visible dashboard state. "
        "Use this information to provide context-aware answers without asking the user for details they already see.\n"
        "\nProvide clear, analytical, and professional guidance based on user queries and available context."
    ),
)

runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)
