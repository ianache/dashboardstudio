"""
Google ADK agent singleton.

The Runner and session_service are module-level singletons — safe for concurrent
reuse per ADK design (discussion #3924). Only session_id varies per request.
"""
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.core.config import get_settings

APP_NAME = "ai-analyst"  # Must match in all session_service calls

settings = get_settings()

session_service = InMemorySessionService()

root_agent = LlmAgent(
    name="bi_analyst",  # underscores required — ADK validates Python identifier
    model=settings.gemini_model,
    instruction=(
        "You are a BI analyst assistant embedded in a dashboard designer tool. "
        "Answer questions about business data clearly and concisely. "
        "When you do not have enough data context to answer precisely, say so honestly."
    ),
)

runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
)
