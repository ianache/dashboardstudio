from fastapi import APIRouter
from app.api.endpoints import (
    users, dashboards, widgets, palettes, data_types, dimensional_models,
    cube_config, llm_config, currencies, data_sources, knowledge_spaces,
    diagram_types, editor_tools, integration_flows, execution_history,
    ml_models,
)

api_router = APIRouter()

api_router.include_router(users.router)
api_router.include_router(dashboards.router)
api_router.include_router(widgets.router)
api_router.include_router(palettes.router)
api_router.include_router(data_types.router)
api_router.include_router(dimensional_models.router)
api_router.include_router(cube_config.router)
api_router.include_router(llm_config.router)
api_router.include_router(currencies.router)
api_router.include_router(data_sources.router)
api_router.include_router(knowledge_spaces.router)
api_router.include_router(diagram_types.router)
api_router.include_router(editor_tools.router)
api_router.include_router(integration_flows.router)
api_router.include_router(execution_history.router)
api_router.include_router(ml_models.router, prefix="/ml-models", tags=["ml-models"])
