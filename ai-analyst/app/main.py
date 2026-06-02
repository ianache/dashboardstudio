"""
AI Analyst FastAPI application.

Endpoints:
  GET  /health  → {status: ok}
  POST /chat    → SSE stream of {type: token|done|error, ...} events
"""
import json
import uuid

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.errors.already_exists_error import AlreadyExistsError

from app.core.config import get_settings
from app.agent import APP_NAME, create_runner, session_service
from app.tools.skills import load_catalog
import app.tools.cube as cube_tool

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
    session_id: str | None = None        # stable dashboard+user key from frontend
    filters: list | None = None           # active CubeJS filter objects (ANALYST-01)
    screen_context: dict | None = None
    context: dict | None = None
    model: str = "gemini-2.5-flash-lite"
    deepseek_api_key: str | None = None


async def ensure_session(user_id: str, session_id: str) -> None:
    """Get-or-create: only create if session does not already exist."""
    existing = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if existing is None:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )


PRICING = {
    "gemini-2.5-flash-lite":          {"input": 0.000000075, "output": 0.0000003},
    "deepseek/deepseek-v4-flash":     {"input": 0.00000027,  "output": 0.0000011},
    "deepseek/deepseek-v4-pro":       {"input": 0.00000055,  "output": 0.00000219},
}


def calculate_cost(model_str: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model_str, {"input": 0.0, "output": 0.0})
    return round(input_tokens * rates["input"] + output_tokens * rates["output"], 6)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def get_models(x_deepseek_api_key: str | None = Header(default=None)):
    models = [
        {"id": "gemini-2.5-flash-lite", "label": "Gemini Flash",
         "provider": "google", "enabled": True}
    ]
    if x_deepseek_api_key:
        models += [
            {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek V4 Flash",
             "provider": "deepseek", "enabled": True},
            {"id": "deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro",
             "provider": "deepseek", "enabled": True},
        ]
    else:
        models += [
            {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek V4 Flash",
             "provider": "deepseek", "enabled": False,
             "disabled_reason": "Add API key in Settings"},
            {"id": "deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro",
             "provider": "deepseek", "enabled": False,
             "disabled_reason": "Add API key in Settings"},
        ]
    return {"models": models}


@app.post("/chat", response_class=EventSourceResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str | None = Header(default=None)
):
    user_id = x_user_id or "default"
    session_id = request.session_id or str(uuid.uuid4())

    # Get-or-create session (safe against AlreadyExistsError)
    await ensure_session(user_id, session_id)

    # Inject screen context if provided by prepending to the user prompt
    prompt = request.message
    screen_ctx = request.context or request.screen_context
    if screen_ctx:
        prompt = f"[CONTEXT] Visible data: {json.dumps(screen_ctx)}\n\nUser request: {prompt}"

    # Inject active dashboard filters: prepend to prompt and store for query_data tool
    if request.filters:
        filter_parts = []
        for f in request.filters:
            member = f.get("member", "")
            op = f.get("operator", "")
            vals = f.get("values", [])
            filter_parts.append(f"{member} {op} {vals}")
        filter_str = "[ACTIVE FILTERS] " + "; ".join(filter_parts)
        prompt = filter_str + "\n\n" + prompt
        cube_tool._active_filters = request.filters
    else:
        cube_tool._active_filters = None

    active_runner = create_runner(request.model, request.deepseek_api_key)
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    try:
        async for event in active_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            ),
            run_config=run_config,
        ):
            # Emit token events for partial text chunks
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield ServerSentEvent(
                            data={"type": "answer", "content": part.text}
                        )

            # Emit done event on final response with usage metadata
            if event.is_final_response():
                input_t = 0
                output_t = 0
                if event.usage_metadata:
                    input_t = getattr(event.usage_metadata, "prompt_token_count", 0) or 0
                    output_t = getattr(event.usage_metadata, "candidates_token_count", 0) or 0
                cost = calculate_cost(request.model, input_t, output_t)
                yield ServerSentEvent(
                    data={"type": "usage", "data": {
                        "input_tokens": input_t,
                        "output_tokens": output_t,
                        "cost": cost
                    }}
                )
                yield ServerSentEvent(
                    data={"type": "done"}
                )

    except Exception as e:
        # Inline error — do not disconnect with HTTP 500
        yield ServerSentEvent(
            data={"type": "error", "message": str(e)}
        )
