# BI Portal Backend

Backend API para BI Portal Dashboard construido con FastAPI, SQLAlchemy y Alembic.

## Requisitos

- Python 3.11+
- PostgreSQL
- uv (gestor de paquetes)

## Configuración

1. Copiar `.env.example` a `.env` y configurar las variables:

```bash
cp .env.example .env
```

2. Instalar dependencias:

```bash
cd backend
uv sync
```

## Uso

### Desarrollo

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Migraciones

Generar nueva migración:
```bash
uv run alembic revision --autogenerate -m "create users table"
```

Aplicar migraciones:
```bash
uv run alembic upgrade head
```

## Estructura

```
backend/
├── app/
│   ├── api/
│   │   └── endpoints/    # Endpoints API
│   ├── core/             # Configuración, DB, seguridad
│   ├── models/           # Modelos SQLAlchemy
│   └── schemas/          # Esquemas Pydantic
├── alembic/
│   └── versions/         # Migraciones
└── pyproject.toml        # Dependencias uv
```

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| POSTGRES_HOST | Host PostgreSQL | localhost |
| POSTGRES_PORT | Puerto PostgreSQL | 5432 |
| POSTGRES_USER | Usuario PostgreSQL | biportal |
| POSTGRES_PASSWORD | Contraseña PostgreSQL | biportal |
| POSTGRES_DB | Base de datos | biportal |
| POSTGRES_SCHEMA | Esquema PostgreSQL | biportal |
| KEYCLOAK_URL | URL Keycloak | https://oauth2.qa.comsatel.com.pe |
| KEYCLOAK_REALM | Realm Keycloak | Apps |
| KEYCLOAK_CLIENT_ID | Client ID | bi-backend |
| APP_HOST | Host aplicación | 0.0.0.0 |
| APP_PORT | Puerto aplicación | 8000 |
| DEBUG | Modo debug | false |

## API Endpoints

- `GET /health` - Health check
- `GET /api/v1/users/me` - Usuario actual
- `GET /api/v1/dashboards` - Listar dashboards
- `POST /api/v1/dashboards` - Crear dashboard
- `GET /api/v1/palettes` - Listar paletas de colores
- `GET /api/v1/data-types` - Listar tipos de datos
- `GET /api/v1/dimensional-models` - Listar modelos dimensionales
- `GET /api/v1/cube-config` - Configuración CubeJS