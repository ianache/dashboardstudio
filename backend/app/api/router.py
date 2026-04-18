from fastapi import APIRouter
from app.api.endpoints import users, dashboards, widgets, palettes, data_types, dimensional_models, cube_config, llm_config, currencies

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