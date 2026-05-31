import asyncio
import logging
import httpx
import jinja2
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def execute_llm_node(props: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    """
    Executes an LLM completion call using an OpenAI-compatible endpoint.
    Includes automatic retries for HTTP 429 errors.
    """
    url = props.get("url")
    api_key = props.get("api_key")
    
    # Model resolution: Node Prop > Connection Prop > Default
    model = props.get("model")
    if not model or str(model).strip() == "":
        model = "gpt-4o"
    
    system_prompt = props.get("system_prompt") or "You are a helpful assistant."
    user_prompt_template = props.get("user_prompt") or "{{payload}}"
    temperature = float(props.get("temperature", 0.7))
    max_tokens = int(props.get("max_tokens", 1024))

    if not url:
        return {"success": False, "error": "LLM Connection has no URL configured"}

    # 1. Render User Prompt using Jinja2
    try:
        # Wrap input in a consistent context
        if isinstance(ctx, dict) and "payload" in ctx:
            context = ctx
        else:
            context = {"payload": ctx, "data": ctx, "variables": {}}
            
        template = jinja2.Template(user_prompt_template)
        rendered_user_prompt = template.render(context)
    except Exception as e:
        return {"success": False, "error": f"Failed to render user prompt: {str(e)}"}

    # 2. Prepare OpenAI Payload
    endpoint = url.rstrip('/') + "/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    llm_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": rendered_user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # 3. Call API with Retries
    max_retries = 3
    retry_delays = [1, 2, 4]  # Exponential backoff

    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(endpoint, json=llm_payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"success": True, "output": content}
                
                if response.status_code == 429:
                    if attempt < max_retries:
                        # Try to get retry-after header
                        retry_after = response.headers.get("retry-after")
                        wait_time = float(retry_after) if retry_after and retry_after.isdigit() else retry_delays[attempt]
                        logger.warning(f"LLM Rate Limited (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return {"success": False, "error": "LLM Rate Limit exceeded after multiple retries."}
                
                # Other error
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"].get("message", error_detail)
                except:
                    pass
                
                return {"success": False, "error": f"LLM API Error {response.status_code}: {error_detail}"}

            except httpx.RequestError as e:
                if attempt < max_retries:
                    wait_time = retry_delays[attempt]
                    logger.warning(f"LLM Connection Error: {str(e)}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                return {"success": False, "error": f"LLM Connection Failed: {str(e)}"}
            except Exception as e:
                return {"success": False, "error": f"Unexpected LLM Error: {str(e)}"}

    return {"success": False, "error": "Unknown error in LLM execution"}
