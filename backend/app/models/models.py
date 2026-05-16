from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(20), default="viewer")
    avatar = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dashboards = relationship("Dashboard", back_populates="owner", foreign_keys="Dashboard.created_by")
    assigned_dashboards = relationship("DashboardAssignment", back_populates="user")


class Dashboard(Base):
    __tablename__ = "dashboards"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filters = Column(JSON, default=[])

    owner = relationship("User", back_populates="dashboards", foreign_keys=[created_by])
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")
    assignments = relationship("DashboardAssignment", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardAssignment(Base):
    __tablename__ = "dashboard_assignments"
    __table_args__ = {"schema": "biportal"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(String(50), ForeignKey("biportal.dashboards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), ForeignKey("biportal.users.id", ondelete="CASCADE"), nullable=False)

    dashboard = relationship("Dashboard", back_populates="assignments")
    user = relationship("User", back_populates="assigned_dashboards")


class Widget(Base):
    __tablename__ = "widgets"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    dashboard_id = Column(String(50), ForeignKey("biportal.dashboards.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    chart_type = Column(String(50), default="bar")
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    position_w = Column(Integer, default=6)
    position_h = Column(Integer, default=3)
    cube_query = Column(JSON, default={})
    chart_options = Column(JSON, default={})
    use_mock_data = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dashboard = relationship("Dashboard", back_populates="widgets")

    @property
    def position(self):
        return {"x": self.position_x, "y": self.position_y, "w": self.position_w, "h": self.position_h}


class ColorPalette(Base):
    __tablename__ = "color_palettes"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    label = Column(String(100), nullable=False)
    colors = Column(JSON, default=[])
    is_default = Column(Boolean, default=False)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataType(Base):
    __tablename__ = "data_types"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    base_type = Column(String(50), nullable=False)
    size = Column(Integer, nullable=True)
    precision = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Currency(Base):
    __tablename__ = "currencies"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    code = Column(String(10), nullable=False)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)


class DimensionalModel(Base):
    __tablename__ = "dimensional_models"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_global = Column(Boolean, default=False)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    nodes = Column(JSON, default=[])
    relationships = Column(JSON, default=[])
    diagrams = Column(JSON, default=[])

    owner = relationship("User", foreign_keys=[created_by])


class CubeConfig(Base):
    __tablename__ = "cube_config"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    api_url = Column(String(500), nullable=False)
    api_token = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LlmConfig(Base):
    __tablename__ = "llm_config"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    provider = Column(String(50), nullable=False)  # anthropic, gemini, moonshot, groq
    api_key = Column(String(500), nullable=False)  # Encrypted
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # qdrant, neo4j, postgresql, mysql, etc.
    connection_url = Column(String(500), nullable=True)  # stores JSON config blob
    username = Column(String(100), nullable=True)
    password = Column(String(500), nullable=True)  # Encrypted (legacy)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeSpace(Base):
    __tablename__ = "knowledge_spaces"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    config = Column(JSON, default={})
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DiagramType(Base):
    __tablename__ = "diagram_types"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=False, default="schema")
    color = Column(String(20), nullable=False, default="#2563eb")
    ai_assist_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EditorTool(Base):
    __tablename__ = "editor_tools"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subtitle = Column(String(200), nullable=True)
    icon = Column(String(50), nullable=False, default="storage")
    category = Column(String(50), nullable=False, default="source")
    applicable_diagram_types = Column(JSON, default=list)
    prop_defs = Column(JSON, default=dict)
    default_props = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationFlow(Base):
    __tablename__ = "integration_flows"
    __table_args__ = {"schema": "biportal"}

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    diagram_type = Column(String(50), nullable=False, default="data-integration")
    status = Column(String(20), nullable=False, default="draft")
    flow_type = Column(String(50), nullable=True)
    cron_expression = Column(String(100), nullable=True)
    log_level = Column(String(20), default='summary')
    source_system = Column(String(100), nullable=True)
    target_system = Column(String(100), nullable=True)
    flow_nodes = Column(JSON, nullable=False, default=list)
    flow_connections = Column(JSON, nullable=False, default=list)
    flow_metadata = Column(JSON, nullable=False, default=dict)
    flow_notes = Column(JSON, nullable=False, default=list)
    last_run = Column(DateTime, nullable=True)
    last_run_success = Column(Boolean, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_by = Column(String(50), ForeignKey("biportal.users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    executions = relationship("ExecutionHistory", back_populates="flow", cascade="all, delete-orphan")


class ExecutionHistory(Base):
    __tablename__ = "execution_history"
    __table_args__ = {"schema": "biportal"}
    id = Column(String(50), primary_key=True)
    flow_id = Column(String(50), ForeignKey("biportal.integration_flows.id"), nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)
    
    flow = relationship("IntegrationFlow", back_populates="executions")
    node_logs = relationship("NodeExecutionLogs", back_populates="execution", cascade="all, delete-orphan")


class NodeExecutionLogs(Base):
    __tablename__ = "node_execution_logs"
    __table_args__ = {"schema": "biportal"}
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(50), ForeignKey("biportal.execution_history.id"), nullable=False)
    node_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    execution = relationship("ExecutionHistory", back_populates="node_logs")

