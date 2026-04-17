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
