# Phase 44: AI Analyst Skills - Research

**Researched:** 2026-05-31
**Domain:** Google ADK Tool Integration, CubeJS Python API, Skills Catalog
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from REQUIREMENTS.md)

### Agent Capabilities
- **AGENT-01**: Agent must interpret visible dashboard chart data (screen context).
- **AGENT-02**: Agent must execute ad-hoc CubeJS queries.
- **AGENT-03**: Agent must trigger skills from a dynamically loaded catalog.

### AI Service
- **SVC-02**: Integrate CubeJS as an agent tool.
- **SVC-03**: Load skills catalog (catalog.yaml) at startup.
</user_constraints>

---

## Summary

Phase 44 transforms the `ai-analyst` from a generic chatbot into a functional platform component by adding two primary tools: a CubeJS query tool for data analysis and a Skills Catalog tool for operational tasks.

The integration uses the **Google ADK Python Tool** pattern: standard Python functions with descriptive docstrings and type hints. These functions are passed to the `LlmAgent(tools=[...])` constructor.

**CubeJS Integration:** Will use the `httpx` client to hit the `/v1/load` REST endpoint. Authentication will be handled via JWT (using `PyJWT` if needed or a pre-shared token for dev). The tool will accept a JSON query object matching the CubeJS specification (measures, dimensions, timeDimensions, filters).

**Skills Catalog Integration:** The service will fetch `catalog.yaml` from a remote URL at startup. This catalog will be parsed using `PyYAML`. The agent will be given a tool to search and execute these skills by name.

**Screen Context (AGENT-01):** The `/chat` request schema will be extended to include `screen_context` (a JSON object representing the currently visible dashboard data). This context will be injected into the agent's session as a hidden "system" or "context" message before the user query, ensuring the agent can answer questions about "this chart" without further tool calls.

---

## Standard Stack

### Core Integration
- **google-adk 2.1.0**: Specifically `LlmAgent` and `Runner`.
- **httpx**: For async API calls to CubeJS and fetching the catalog.
- **PyYAML**: For parsing the skills catalog.
- **PyJWT**: (Optional) For generating CubeJS security tokens if required.

---

## Architecture Patterns

### Pattern 1: Dynamic Tool Loading
Tools that depend on external configurations (like the catalog) should be initialized after the configuration is fetched.

```python
# app/tools/skills.py
import yaml
import httpx

async def load_catalog(url: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        return yaml.safe_load(res.text)

def execute_skill(skill_name: str, params: dict):
    """
    Executes a specific skill from the platform catalog.
    
    Args:
        skill_name: The unique identifier of the skill.
        params: Key-value pairs of parameters required by the skill.
    """
    # Logic to trigger integration flow or platform action
    return f"Skill {skill_name} executed successfully."
```

### Pattern 2: CubeJS Query Tool
A tool that maps natural language intents to CubeJS queries.

```python
# app/tools/cube.py
async def run_analytics_query(query: dict):
    """
    Executes a CubeJS query to fetch business data.
    
    Args:
        query: A valid CubeJS query object with 'measures' and 'dimensions'.
    """
    # Call CubeJS /v1/load
    return {"data": [...]}
```

---

## Pitfalls to Avoid

- **Docstring Precision:** If the docstrings are too vague, Gemini might not call the tools. They must be highly descriptive about the CubeJS schema and available skills.
- **JWT Expiry:** Ensure CubeJS tokens don't expire mid-session.
- **Context Size:** If `screen_context` is massive (thousands of rows), it could blow the context window or cause latency. We should limit/summarize data on the frontend if needed.

---

## Next Steps

1. **Plan 01**: Implement CubeJS tool and extend `/chat` schema for screen context.
2. **Plan 02**: Implement Skills Catalog loading and execution tool.
