import json
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime


class UserBase(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "viewer"


class UserCreate(UserBase):
    pass


class UserProvision(BaseModel):
    """Upsert a user record from an external source (e.g. Keycloak)"""
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Position(BaseModel):
    x: int = 0
    y: int = 0
    w: int = 6
    h: int = 3


class CubeQuery(BaseModel):
    measures: List[dict] = []
    dimensions: List[dict] = []
    time_dimension: Optional[dict] = None
    filters: List[dict] = []
    limit: int = 100


class WidgetBase(BaseModel):
    title: str = "Nuevo Gráfico"
    chart_type: str = "bar"
    position: Position = Position()
    cube_query: CubeQuery = CubeQuery()
    chart_options: dict = {}
    use_mock_data: bool = False


class WidgetCreate(WidgetBase):
    pass


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    chart_type: Optional[str] = None
    position: Optional[dict] = None
    cube_query: Optional[dict] = None
    chart_options: Optional[dict] = None
    use_mock_data: Optional[bool] = None


class WidgetResponse(WidgetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DashboardBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    filters: List[dict] = []


class DashboardCreate(DashboardBase):
    pass


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    filters: Optional[List[dict]] = None


class DashboardResponse(DashboardBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    widgets: List[WidgetResponse] = []


class DashboardWithAssignments(DashboardResponse):
    assigned_users: List[str] = []


class DashboardAssignmentRequest(BaseModel):
    user_ids: List[str]


class ColorPaletteBase(BaseModel):
    label: str
    colors: List[str]
    is_default: bool = False

    @field_validator('colors', mode='before')
    @classmethod
    def parse_colors(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
        return v


class ColorPaletteCreate(ColorPaletteBase):
    pass


class ColorPaletteUpdate(BaseModel):
    label: Optional[str] = None
    colors: Optional[List[str]] = None
    is_default: Optional[bool] = None


class ColorPaletteResponse(ColorPaletteBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DataTypeBase(BaseModel):
    name: str
    base_type: str
    size: Optional[int] = None
    precision: Optional[int] = None
    description: Optional[str] = None
    is_builtin: bool = False


class DataTypeCreate(DataTypeBase):
    pass


class DataTypeUpdate(BaseModel):
    name: Optional[str] = None
    base_type: Optional[str] = None
    size: Optional[int] = None
    precision: Optional[int] = None
    description: Optional[str] = None


class DataTypeResponse(DataTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CurrencyBase(BaseModel):
    code: str
    symbol: str
    name: str
    is_active: bool = True


class CurrencyResponse(CurrencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class DimensionalModelNode(BaseModel):
    id: str
    type: str
    name: str
    icon: Optional[str] = ""
    description: Optional[str] = ""
    x: float = 100
    y: float = 100
    global_ref: Optional[dict] = None
    fields: List[dict] = []


class DimensionalModelRelationship(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    cardinality: str = "1:N"


class DimensionalModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_global: bool = False
    nodes: List[DimensionalModelNode] = []
    relationships: List[DimensionalModelRelationship] = []
    diagrams: List[dict] = []


class DimensionalModelCreate(DimensionalModelBase):
    pass


class DimensionalModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_global: Optional[bool] = None
    nodes: Optional[List[dict]] = None
    relationships: Optional[List[dict]] = None
    diagrams: Optional[List[dict]] = None


class DimensionalModelResponse(DimensionalModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CubeConfigBase(BaseModel):
    name: str
    api_url: str
    api_token: Optional[str] = None
    is_active: bool = True


class CubeConfigCreate(CubeConfigBase):
    pass


class CubeConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    api_token: Optional[str] = None
    is_active: Optional[bool] = None


class CubeConfigResponse(CubeConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


# LLM Configuration Schemas
class LlmProviderInfo(BaseModel):
    id: str
    label: str
    icon: str
    api_key_label: str
    api_key_placeholder: str
    docs_url: str


class LlmConfigBase(BaseModel):
    provider: str
    api_key: str


class LlmConfigCreate(LlmConfigBase):
    pass


class LlmConfigResponse(LlmConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# DataSource Schemas
class DataSourceBase(BaseModel):
    name: str
    type: str  # qdrant, neo4j, postgresql, mysql, etc.
    connection_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    connection_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    connection_url: str
    username: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# KnowledgeSpace Schemas
class KnowledgeSpaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict = {}


class KnowledgeSpaceCreate(KnowledgeSpaceBase):
    pass


class KnowledgeSpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


class KnowledgeSpaceResponse(KnowledgeSpaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ── DiagramType ────────────────────────────────────────────────────────────────

class DiagramTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: str = "schema"
    color: str = "#2563eb"
    ai_assist_prompt: Optional[str] = None

class DiagramTypeCreate(DiagramTypeBase):
    id: str

class DiagramTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    ai_assist_prompt: Optional[str] = None

class DiagramTypeResponse(DiagramTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── EditorTool ─────────────────────────────────────────────────────────────────

class EditorToolBase(BaseModel):
    type: str
    name: str
    description: Optional[str] = None
    subtitle: Optional[str] = None
    icon: str = "storage"
    category: str = "source"
    applicable_diagram_types: List[str] = []
    prop_defs: dict = {}
    default_props: dict = {}

class EditorToolCreate(EditorToolBase):
    pass

class EditorToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    applicable_diagram_types: Optional[List[str]] = None
    prop_defs: Optional[dict] = None
    default_props: Optional[dict] = None

class EditorToolResponse(EditorToolBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── IntegrationFlow ────────────────────────────────────────────────────────────

class IntegrationFlowBase(BaseModel):
    name: str
    description: Optional[str] = None
    diagram_type: str = "data-integration"
    status: str = "draft"
    flow_type: Optional[str] = None
    cron_expression: Optional[str] = None
    log_level: Optional[str] = "summary"
    source_system: Optional[str] = None
    target_system: Optional[str] = None

class IntegrationFlowCreate(IntegrationFlowBase):
    flow_nodes: List[dict] = []
    flow_connections: List[dict] = []
    flow_metadata: dict = {}

class IntegrationFlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    flow_type: Optional[str] = None
    cron_expression: Optional[str] = None
    log_level: Optional[str] = None
    source_system: Optional[str] = None
    target_system: Optional[str] = None
    flow_nodes: Optional[List[dict]] = None
    flow_connections: Optional[List[dict]] = None
    flow_metadata: Optional[dict] = None
    last_run_success: Optional[bool] = None

class IntegrationFlowResponse(IntegrationFlowBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    flow_nodes: List[dict] = []
    flow_connections: List[dict] = []
    flow_metadata: dict = {}
    last_run: Optional[datetime] = None
    last_run_success: Optional[bool] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── ExecutionHistory ──────────────────────────────────────────────────────────

class NodeExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    node_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None

class ExecutionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    flow_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None

class ExecutionDetailResponse(ExecutionHistoryResponse):
    node_logs: List[NodeExecutionLogResponse] = []
