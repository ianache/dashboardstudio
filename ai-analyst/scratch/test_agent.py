import asyncio
import os
from dotenv import load_dotenv

# Ensure environment is loaded
load_dotenv(".env-ai-analyst", override=True)

from app.agent import runner, session_service, APP_NAME
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

async def main():
    session_id = "test-session-123"
    
    # Pre-create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="default",
        session_id=session_id,
    )
    
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
    print("Running agent with prompt: 'generar un insight'...")
    try:
        async for event in runner.run_async(
            user_id="default",
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text="generar un insight")],
            ),
            run_config=run_config,
        ):
            # Print basic event representation
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"Token: {part.text}")
            if event.is_final_response():
                print("\nFinal Response received.")
    except Exception as e:
        print(f"\nCRITICAL ERROR EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
