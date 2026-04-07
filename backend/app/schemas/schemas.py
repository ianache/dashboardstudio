from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "viewer"


class UserCreate(UserBase):
    pass


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
    created_at: datetime
    updated_at: datetime


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
    position: Optional[Position] = None
    cube_query: Optional[dict] = None
    chart_options: Optional[dict] = None
    use_mock_data: Optional[bool] = None


class WidgetResponse(WidgetBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
    updated_at: datetime
    widgets: List[WidgetResponse] = []


class DashboardWithAssignments(DashboardResponse):
    assigned_users: List[str] = []


class DashboardAssignmentRequest(BaseModel):
    user_ids: List[str]


class ColorPaletteBase(BaseModel):
    label: str
    colors: List[str]
    is_default: bool = False


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
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
    updated_at: datetime


class DimensionalModelNode(BaseModel):
    id: str
    type: str
    name: str
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


class DimensionalModelCreate(DimensionalModelBase):
    pass


class DimensionalModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_global: Optional[bool] = None
    nodes: Optional[List[dict]] = None
    relationships: Optional[List[dict]] = None


class DimensionalModelResponse(DimensionalModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str