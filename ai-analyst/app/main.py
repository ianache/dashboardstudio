"""
AI Analyst FastAPI application.

Endpoints:
  GET  /health  → {status: ok}
  POST /chat    → SSE stream of {type: token|done|error, ...} events
"""
import json
import uuid
import logging

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from google import genai
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
    groq_api_key: str | None = None


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
    "groq/llama-3.3-70b-versatile":   {"input": 0.00000059,  "output": 0.00000079},
}

CONTEXT_SIZE_LIMIT = 200_000  # 200 KB in bytes
FALLBACK_SUMMARY_MODEL = "gemini-2.5-flash-lite"


def calculate_cost(model_str: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model_str, {"input": 0.0, "output": 0.0})
    return round(input_tokens * rates["input"] + output_tokens * rates["output"], 6)


def _session_byte_size(user_id: str, session_id: str) -> int:
    """Return the byte size of the serialized session, or 0 if not found."""
    try:
        svc_sessions = session_service.sessions
        session = svc_sessions[APP_NAME][user_id][session_id]
        return len(json.dumps(session.model_dump()).encode("utf-8"))
    except (KeyError, Exception):
        return 0


def _events_to_text(events) -> str:
    """Convert ADK session events to a plain text summary for the LLM."""
    lines = []
    for ev in events:
        if not ev.content or not ev.content.parts:
            continue
        role = ev.content.role or "unknown"
        for part in ev.content.parts:
            if hasattr(part, "text") and part.text:
                lines.append(f"{role.upper()}: {part.text[:500]}")  # cap per part
    return "\n".join(lines)


async def _summarize_session(user_id: str, session_id: str, model: str = FALLBACK_SUMMARY_MODEL) -> str:
    """
    Summarize the current session history and clear the session events.
    Returns the summary text to be injected into the next prompt.
    Called only when session byte size exceeds CONTEXT_SIZE_LIMIT.

    Uses `model` for summarization if it is a Gemini model; otherwise falls back
    to FALLBACK_SUMMARY_MODEL since non-Gemini models require ADK runner infrastructure.
    """
    logger = logging.getLogger(__name__)

    try:
        svc_sessions = session_service.sessions
        session = svc_sessions[APP_NAME][user_id][session_id]
        history_text = _events_to_text(session.events)
    except (KeyError, Exception):
        return ""

    summary_prompt = (
        "Summarize the following BI analysis conversation concisely. "
        "Preserve: key metrics discussed, conclusions reached, specific data values found, "
        "and any open questions or tasks. Be brief but complete.\n\n"
        + history_text
    )

    # Use the active model when it is a Gemini model; otherwise fall back
    summary_model = model if model.startswith("gemini") else FALLBACK_SUMMARY_MODEL
    logger.info(f"Summarizing session {session_id} using model {summary_model}")

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=summary_model,
            contents=summary_prompt
        )
        summary_text = response.text or ""
    except Exception as e:
        summary_text = f"[Prior conversation summarized — details unavailable: {e}]"

    # Clear session events using direct dict mutation
    # (InMemorySessionService has no delete_session() method)
    try:
        svc_sessions[APP_NAME][user_id][session_id].events.clear()
    except (KeyError, Exception):
        pass

    return summary_text


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def get_models(
    x_deepseek_api_key: str | None = Header(default=None),
    x_groq_api_key: str | None = Header(default=None),
):
    models = [
        {"id": "gemini-2.5-flash-lite", "label": "Gemini Flash",
         "provider": "google", "enabled": True}
    ]
    # ── DeepSeek ──────────────────────────────────────────────────────────────
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
    # ── Groq ──────────────────────────────────────────────────────────────────
    if x_groq_api_key:
        models += [
            {"id": "groq/llama-3.3-70b-versatile", "label": "Llama 3.3 70B",
             "provider": "groq", "enabled": True},
        ]
    else:
        models += [
            {"id": "groq/llama-3.3-70b-versatile", "label": "Llama 3.3 70B",
             "provider": "groq", "enabled": False,
             "disabled_reason": "Add Groq API key in Settings"},
        ]
    return {"models": models}


@app.post("/chat", response_class=EventSourceResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str | None = Header(default=None)
):
    user_id = x_user_id or "default"
    session_id = request.session_id or str(uuid.uuid4())

    logger = logging.getLogger(__name__)
    logger.info(f"Chat request - model: {request.model}, session: {session_id}")
    logger.info(f"Message length: {len(request.message)}, context keys: {list((request.context or {}).keys()) if request.context else None}")

    # Get-or-create session (safe against AlreadyExistsError)
    await ensure_session(user_id, session_id)

    # Check session size and summarize if needed (before building prompt)
    summary_prefix = ""
    if _session_byte_size(user_id, session_id) > CONTEXT_SIZE_LIMIT:
        summary_text = await _summarize_session(user_id, session_id, model=request.model)
        if summary_text:
            summary_prefix = f"[CONTEXT SUMMARY — prior conversation] {summary_text}\n\n"

    # Inject screen context if provided by prepending to the user prompt
    prompt = request.message
    screen_ctx = request.context or request.screen_context
    if screen_ctx:
        # Build a clean, compact representation for the model
        ctx_parts = []
        
        if screen_ctx.get("dashboard"):
            d = screen_ctx["dashboard"]
            ctx_parts.append(f"Dashboard: {d.get('name', 'Untitled')}")
            if d.get("description"):
                ctx_parts.append(f"Description: {d.get('description')}")
        
        if screen_ctx.get("widgets"):
            ctx_parts.append("\nWidgets in this dashboard:")
            for w in screen_ctx["widgets"]:
                widget_info = f"- {w.get('title', 'Untitled')} ({w.get('type', 'unknown')})"
                if w.get("cubeQuery"):
                    cq = w["cubeQuery"]
                    if cq.get("measures"):
                        widget_info += f" | Measures: {', '.join(m.get('label') or m.get('key', '') for m in cq['measures'][:3])}"
                    if cq.get("dimensions"):
                        widget_info += f" | Dimensions: {', '.join(d.get('label') or d.get('key', '') for d in cq['dimensions'][:3])}"
                if w.get("data") and len(w["data"]) > 0:
                    # Include a summary of the data, not raw values
                    data_sample = w["data"][:3]
                    data_labels = [str(d.get("label", "")) for d in data_sample]
                    widget_info += f" | Data: {data_labels}"
                    if len(w["data"]) > 3:
                        widget_info += f" (+{len(w['data']) - 3} more rows)"
                ctx_parts.append(widget_info)
        
        ctx_str = "\n".join(ctx_parts)
        logger.info(f"Built compact context ({len(ctx_str)} chars)")
        
        # Truncate if still too large
        MAX_CTX_LEN = 8000
        if len(ctx_str) > MAX_CTX_LEN:
            ctx_str = ctx_str[:MAX_CTX_LEN] + "\n...(context truncated)"
        
        prompt = f"[CONTEXT]\n{ctx_str}\n\n[User Request]\n{prompt}"

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

    # Prepend context summary if summarization occurred
    if summary_prefix:
        prompt = summary_prefix + prompt

    active_runner = create_runner(request.model, request.deepseek_api_key, request.groq_api_key)
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    try:
        # Emit context_summarized event BEFORE the agent response if summary was done
        if summary_prefix:
            yield ServerSentEvent(data={"type": "context_summarized"})

        text_emitted = False  # track whether any answer chunk was streamed

        async for event in active_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            ),
            run_config=run_config,
        ):
            # Debug log each event
            event_type = "unknown"
            if hasattr(event, 'content') and event.content:
                if event.content.parts:
                    text_part = event.content.parts[0].text if hasattr(event.content.parts[0], 'text') else None
                    event_type = f"text_chunk(len={len(text_part) if text_part else 0})"
                elif hasattr(event.content, 'role'):
                    event_type = f"role={event.content.role}"
            logger.info(f"ADK event: {event_type}, is_final={event.is_final_response() if hasattr(event, 'is_final_response') else 'N/A'}")

            if event.content and event.content.parts:
                for part in event.content.parts:
                    # ── Tool calls → "tool_call" (shown in Analyzing panel) ──
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        yield ServerSentEvent(
                            data={"type": "tool_call", "name": fc.name,
                                  "args": dict(fc.args) if fc.args else {}}
                        )
                    # ── Tool responses → "tool_result" (shown in Analyzing panel) ──
                    elif hasattr(part, "function_response") and part.function_response:
                        fr = part.function_response
                        resp = fr.response if fr.response else {}
                        # Count rows if present to keep payload small
                        rows = len(resp.get("data", [])) if isinstance(resp, dict) else None
                        yield ServerSentEvent(
                            data={"type": "tool_result", "name": fr.name,
                                  "rows": rows}
                        )
                    # ── Text chunks ──
                    elif hasattr(part, "text") and part.text:
                        if event.is_final_response():
                            # Final response text → "answer" (Results panel)
                            text_emitted = True
                            yield ServerSentEvent(
                                data={"type": "answer", "content": part.text}
                            )
                        else:
                            # Intermediate streaming chunks → "thinking" (Analyzing panel)
                            yield ServerSentEvent(
                                data={"type": "thinking", "content": part.text}
                            )

            # Fallback: non-streaming model only emits text at the final event.
            # If no answer was emitted yet on is_final, we already handled it above
            # (the final text loop covers it). Emit usage + done.
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
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        # Truncate long error messages and replace newlines with spaces for SSE
        error_msg = error_msg.replace('\n', ' ').replace('\r', ' ')
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        yield ServerSentEvent(
            data={"type": "error", "message": error_msg}
        )
