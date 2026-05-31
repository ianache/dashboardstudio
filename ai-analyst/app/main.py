"""
AI Analyst FastAPI application.

Endpoints:
  GET  /health  → {status: ok}
  POST /chat    → SSE stream of {type: token|done|error, ...} events
"""
import json
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

from app.core.config import get_settings
from app.agent import APP_NAME, runner, session_service
from app.tools.skills import load_catalog

settings = get_settings()

app = FastAPI(title="AI Analyst Service", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    await load_catalog()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    screen_context: dict | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_class=EventSourceResponse)
async def chat(request: ChatRequest):
    session_id = str(uuid.uuid4())

    # Create a fresh session per request — Phase 43 has no conversation history
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="default",
        session_id=session_id,
    )

    # Inject screen context if provided
    if request.screen_context:
        await session_service.append_message(
            app_name=APP_NAME,
            user_id="default",
            session_id=session_id,
            role="user",
            text=f"[CONTEXT] Visible data: {json.dumps(request.screen_context)}",
        )

    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    try:
        async for event in runner.run_async(
            user_id="default",
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=request.message)],
            ),
            run_config=run_config,
        ):
            # Emit token events for partial text chunks
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield ServerSentEvent(
                            data=json.dumps({"type": "token", "text": part.text})
                        )

            # Emit done event on final response with usage metadata
            if event.is_final_response():
                usage = {"input_tokens": 0, "output_tokens": 0}
                if event.usage_metadata:
                    usage["input_tokens"] = getattr(
                        event.usage_metadata, "prompt_token_count", 0
                    ) or 0
                    usage["output_tokens"] = getattr(
                        event.usage_metadata, "candidates_token_count", 0
                    ) or 0
                yield ServerSentEvent(
                    data=json.dumps({"type": "done", "usage": usage})
                )

    except Exception as e:
        # Inline error — do not disconnect with HTTP 500
        yield ServerSentEvent(
            data=json.dumps({"type": "error", "message": str(e)})
        )
