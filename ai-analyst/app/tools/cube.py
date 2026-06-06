import re
import ast
import json
import httpx
import jwt
import time
import logging
from contextvars import ContextVar
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_MEMBER_PATTERN = re.compile(r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$")

_VALID_CUBE_OPERATORS = {
    "equals", "notEquals",
    "contains", "notContains",
    "startsWith", "endsWith",
    "gt", "gte", "lt", "lte",
    "set", "notSet",
    "inDateRange", "notInDateRange",
    "beforeDate", "afterDate",
}

_OPERATOR_ALIASES = {
    "like": "contains",
    "ilike": "contains",
    "not like": "notContains",
    "not_like": "notContains",
    "in": "equals",
    "not in": "notEquals",
    "not_in": "notEquals",
    "is": "equals",
    "is not": "notEquals",
    "is_not": "notEquals",
    "before": "beforeDate",
    "after": "afterDate",
    "between": "inDateRange",
    "not between": "notInDateRange",
}

# Module-level variable set per request by main.py
_active_filters: list | None = None

# Request-scoped custom label/attribute mappings (ContextVar)
_custom_mappings: ContextVar[dict[str, str]] = ContextVar("custom_mappings", default={})


def normalize_key_string(s: str) -> str:
    """Remove spaces, underscores, hyphens, and dots, and convert to lowercase."""
    return re.sub(r"[\s_\-\.]", "", s).lower()


def set_custom_mappings_from_context(screen_ctx: dict | None) -> None:
    """
    Extracts custom label-to-key mappings from widgets in the screen context
    and sets them in a request-scoped ContextVar.
    """
    if not screen_ctx:
        _custom_mappings.set({})
        return

    mappings = {}
    widgets = screen_ctx.get("widgets") or []
    for w in widgets:
        if not isinstance(w, dict):
            continue
        cq = w.get("cubeQuery")
        if not isinstance(cq, dict):
            continue
            
        items = []
        if isinstance(cq.get("measures"), list):
            items.extend(cq["measures"])
        if isinstance(cq.get("dimensions"), list):
            items.extend(cq["dimensions"])
            
        td = cq.get("timeDimension") or cq.get("timeDimensions")
        if isinstance(td, list):
            items.extend(td)
        elif isinstance(td, dict):
            items.append(td)
            
        for item in items:
            if not isinstance(item, dict):
                continue
                
            physical_key = item.get("key") or item.get("dimension") or item.get("member") or item.get("field") or item.get("column")
            label = item.get("label") or item.get("title") or item.get("name")
            
            if physical_key:
                physical_key = str(physical_key).strip()
                
                # Extract cube name and field
                cube_name = ""
                field = physical_key
                if "." in physical_key:
                    cube_name, field = physical_key.split(".", 1)
                
                # Register physical key mapping variants
                mappings[physical_key.lower()] = physical_key
                mappings[normalize_key_string(physical_key)] = physical_key
                
                # Register field part mapping variants
                mappings[field.lower()] = physical_key
                mappings[normalize_key_string(field)] = physical_key
                
                if label:
                    label = str(label).strip()
                    
                    # Exact lowercase
                    mappings[label.lower()] = physical_key
                    # Cube prefix + label
                    if cube_name:
                        mappings[f"{cube_name}.{label}".lower()] = physical_key
                    
                    # Normalized forms
                    norm_label = normalize_key_string(label)
                    mappings[norm_label] = physical_key
                    if cube_name:
                        norm_cube_label = normalize_key_string(f"{cube_name}.{label}")
                        mappings[norm_cube_label] = physical_key

    logger.info(f"Set {len(mappings)} dynamic custom mappings from screen context.")
    _custom_mappings.set(mappings)


SCHEMA_MAPPING = {
    # fct_horasreportadas
    "total_hours": "fct_horasreportadas.total_hours",
    "cost": "fct_horasreportadas.cost",
    "capacidadTotal": "fct_horasreportadas.capacidadTotal",
    "capacidad_total": "fct_horasreportadas.capacidadTotal",
    "cumplimiento": "fct_horasreportadas.cumplimiento",
    "area": "fct_horasreportadas.area",
    "product": "fct_horasreportadas.product",
    "producto": "fct_horasreportadas.product",
    "client": "fct_horasreportadas.client",
    "cliente": "fct_horasreportadas.client",
    "group": "fct_horasreportadas.group",
    "grupo": "fct_horasreportadas.group",
    "innovation": "fct_horasreportadas.innovation",
    "innovation_area": "fct_horasreportadas.innovation_area",
    "issue_name": "fct_horasreportadas.issue_name",
    "project_name": "fct_horasreportadas.project_name",
    "proyecto": "fct_horasreportadas.project_name",
    "provider": "fct_horasreportadas.provider",
    "reporter": "fct_horasreportadas.reporter",
    "tag_semana": "fct_horasreportadas.tag_semana",
    "reg_date": "fct_horasreportadas.reg_date",
    "anio": "fct_horasreportadas.anio",
    "mes": "fct_horasreportadas.mes",
    "dia": "fct_horasreportadas.dia",
    "day_hours": "fct_horasreportadas.day_hours",
    # Colaborador
    "role": "Colaborador.role",
    "nombre": "Colaborador.nombre",
    "name": "Colaborador.nombre",
    "jornada": "Colaborador.jornada",
    "duracionJornada": "Colaborador.duracionJornada",
    # Sales / Ventas (Leaderboard domain)
    "totalRevenue": "Sales.totalRevenue",
    "unitsSold": "Sales.unitsSold",
    "totalCommissions": "Sales.totalCommissions",
    # Performance
    "attainment": "Performance.attainment",
    "targetUnits": "Performance.targetUnits",
    "prizesPaid": "Performance.prizesPaid",
    "storeBonuses": "Performance.storeBonuses",
    # Leaderboard
    "sellerName": "Leaderboard.sellerName",
    "sellerLevel": "Leaderboard.sellerLevel",
    "storeName": "Leaderboard.storeName",
    "storeCity": "Leaderboard.storeCity",
    "totalSales": "Leaderboard.totalSales",
    "totalEarnings": "Leaderboard.totalEarnings",
    "attainmentScore": "Leaderboard.attainmentScore",
    # Stores
    "nombreTienda": "Stores.name",
    "ruc": "Stores.ruc",
    "city": "Stores.city",
    "ciudad": "Stores.city",
    "region": "Stores.region",
    # VentasConcesionaria
    "montoVenta": "VentasConcesionaria.montoVenta",
    # Concesionaria
    "nombreConcesionaria": "Concesionaria.nombreConcesionaria",
    "canal": "Concesionaria.canal",
    # Vendedor
    "nombreVendedor": "Vendedor.nombreVendedor",
    # Producto (dim)
    "sku": "Producto.sku",
    "nombreProducto": "Producto.nombreProducto",
    "marca": "Producto.marca",
    "modelo": "Producto.modelo",
    "tipoProducto": "Producto.tipoProducto",
    # MedioPago
    "nombreMedioPago": "MedioPago.nombreMedioPago",
    "tipoPago": "MedioPago.tipoPago",
    # ComisionesIncentivos
    "montoComision": "ComisionesIncentivos.montoComision",
    "montoIncentivo": "ComisionesIncentivos.montoIncentivo",
    # fct_sprint_burndown
    "remain": "fct_sprint_burndown.remain",
    "spend": "fct_sprint_burndown.spend",
    "planned_date": "fct_sprint_burndown.planned_date",
    "velocity": "fct_sprint_burndown.velocity",
    # fct_sprint_execution
    "effort": "fct_sprint_execution.effort",
    "date_in_sprint": "fct_sprint_execution.date_in_sprint",
}


# Complete set of valid CubeJS members (from /meta). Used to catch wrong cube prefixes.
_EXTRA_VALID_MEMBERS: set[str] = {
    # Colaborador
    "Colaborador.count", "Colaborador.jornada", "Colaborador.nombre",
    "Colaborador.role", "Colaborador.duracionJornada",
    # fct_horasreportadas
    "fct_horasreportadas.count", "fct_horasreportadas.total_hours",
    "fct_horasreportadas.cost", "fct_horasreportadas.capacidadTotal",
    "fct_horasreportadas.cumplimiento", "fct_horasreportadas.area",
    "fct_horasreportadas.client", "fct_horasreportadas.day_hours",
    "fct_horasreportadas.dia", "fct_horasreportadas.group",
    "fct_horasreportadas.innovation", "fct_horasreportadas.innovation_area",
    "fct_horasreportadas.issue_name", "fct_horasreportadas.mes",
    "fct_horasreportadas.product", "fct_horasreportadas.project_name",
    "fct_horasreportadas.provider", "fct_horasreportadas.reporter",
    "fct_horasreportadas.tag_semana", "fct_horasreportadas.reg_date",
    "fct_horasreportadas.anio",
    # Sales / Leaderboard domain
    "Sales.totalRevenue", "Sales.unitsSold", "Sales.totalCommissions",
    "Sales.date", "Sales.saleMonth",
    "Performance.targetUnits", "Performance.prizesPaid",
    "Performance.storeBonuses", "Performance.attainment",
    "Performance.referenceMonth",
    "Leaderboard.totalSales", "Leaderboard.totalEarnings",
    "Leaderboard.attainmentScore", "Leaderboard.performanceStars",
    "Leaderboard.sellerName", "Leaderboard.sellerLevel",
    "Leaderboard.storeName", "Leaderboard.storeCity",
    "Stores.count", "Stores.name", "Stores.ruc", "Stores.city", "Stores.region",
    "Time.date", "Time.isWeekend", "Time.monthName", "Time.commercialSeason",
    # VentasConcesionaria domain
    "VentasConcesionaria.count", "VentasConcesionaria.montoVenta",
    "VentasConcesionaria.concesionariaId", "VentasConcesionaria.moneda",
    "VentasConcesionaria.fechaOperacion", "VentasConcesionaria.fechaCreacionOv",
    "VentasConcesionaria.date", "VentasConcesionaria.concesionaria",
    "VentasConcesionaria.vendedor", "VentasConcesionaria.tienda",
    "VentasConcesionaria.producto", "VentasConcesionaria.planServicio",
    "VentasConcesionaria.medioPago",
    "Concesionaria.count", "Concesionaria.nombreConcesionaria", "Concesionaria.canal",
    "Tienda.count", "Tienda.nombreTienda", "Tienda.concesionariaId",
    "Vendedor.count", "Vendedor.nombreVendedor", "Vendedor.concesionariaId",
    "Producto.count", "Producto.sku", "Producto.nombreProducto",
    "Producto.marca", "Producto.modelo", "Producto.tipoProducto",
    "MedioPago.count", "MedioPago.nombreMedioPago", "MedioPago.tipoPago",
    "PlanServicio.count", "PlanServicio.descripcionPlan", "PlanServicio.duracionMeses",
    "ComisionesIncentivos.count", "ComisionesIncentivos.montoComision",
    "ComisionesIncentivos.montoIncentivo", "ComisionesIncentivos.tipoMovimiento",
    "ComisionesIncentivos.date", "ComisionesIncentivos.concesionariaId",
    "ComisionesIncentivos.tiendaId", "ComisionesIncentivos.vendedorId",
    "Date.count", "Date.dayOfWeek", "Date.weekNumber", "Date.month",
    "Date.quarter", "Date.fiscalYear", "Date.isWeekend",
    "Date.isHoliday", "Date.isBusinessDay",
    # Sprint cubes
    "fct_sprint_burndown.count", "fct_sprint_burndown.remain",
    "fct_sprint_burndown.spend", "fct_sprint_burndown.guid",
    "fct_sprint_burndown.str_date", "fct_sprint_burndown.velocity",
    "fct_sprint_burndown.planned_date",
    "fct_sprint_execution.count", "fct_sprint_execution.cost",
    "fct_sprint_execution.effort", "fct_sprint_execution.guid",
    "fct_sprint_execution.spend_cost", "fct_sprint_execution.spend_effort",
    "fct_sprint_execution.date_in_sprint",
}

# Union: schema mapping values + extra valid members
VALID_MEMBERS: set[str] = set(SCHEMA_MAPPING.values()) | _EXTRA_VALID_MEMBERS

# field name → correct full Cube.field (built from SCHEMA_MAPPING values first,
# then the rest; SCHEMA_MAPPING takes precedence for ambiguous field names).
_FIELD_TO_MEMBER: dict[str, str] = {}
for _m in _EXTRA_VALID_MEMBERS:
    _field = _m.split(".", 1)[1]
    if _field not in _FIELD_TO_MEMBER:
        _FIELD_TO_MEMBER[_field] = _m
for _m in SCHEMA_MAPPING.values():  # overwrite with SCHEMA_MAPPING (higher priority)
    _field = _m.split(".", 1)[1]
    _FIELD_TO_MEMBER[_field] = _m


def _parse_list_arg(val) -> list:
    """Normalize a value that may be a list, a bare string, or a string repr of a list."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        stripped = val.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
        return [stripped]
    return [str(val)]


def resolve_member(member: str) -> str:
    if not member:
        return member
    member = str(member).strip()

    # Dynamic custom mapping resolution (e.g. from screen context widgets)
    dynamic_map = _custom_mappings.get()
    if dynamic_map:
        # 1. Exact/lowercase lookup
        resolved = dynamic_map.get(member.lower())
        if resolved:
            return resolved
        
        # 2. Normalized lookup
        norm_member = normalize_key_string(member)
        resolved = dynamic_map.get(norm_member)
        if resolved:
            return resolved

    if "." in member:
        parts = member.split(".")
        # Fix triple-part duplicate: Colaborador.Colaborador.name → Colaborador.name
        if len(parts) == 3 and parts[0] == parts[1]:
            member = f"{parts[1]}.{parts[2]}"
        # If already a valid member, return as-is
        if member in VALID_MEMBERS:
            return member
        # Wrong cube prefix: try to find the correct cube using only the field name
        field = member.split(".", 1)[1]
        corrected = _FIELD_TO_MEMBER.get(field)
        if corrected:
            logger.warning(f"Correcting member {member!r} → {corrected!r}")
            return corrected
        # Also try SCHEMA_MAPPING with just the field name
        corrected = SCHEMA_MAPPING.get(field)
        if corrected:
            logger.warning(f"Correcting member {member!r} → {corrected!r}")
            return corrected
        # Unknown — return as-is (will be caught by _MEMBER_PATTERN downstream)
        return member

    # Short name without dot — look up in SCHEMA_MAPPING
    resolved = SCHEMA_MAPPING.get(member)
    if resolved:
        return resolved

    return member


def parse_string_filter(s: str) -> dict | None:
    s = s.strip()
    # Find operators in order of length to avoid partial matches
    operators = [
        (">=", "gte"),
        ("<=", "lte"),
        ("!=", "notEquals"),
        ("=", "equals"),
        (">", "gt"),
        ("<", "lt"),
        (" equals ", "equals"),
        (" notEquals ", "notEquals"),
        (" gte ", "gte"),
        (" lte ", "lte"),
        (" gt ", "gt"),
        (" lt ", "lt"),
        (" contains ", "contains"),
        (" like ", "contains"),
        (" in ", "equals")
    ]
    
    for op_str, op_name in operators:
        if op_str in s:
            parts = s.split(op_str, 1)
            member = resolve_member(parts[0].strip())
            val_str = parts[1].strip()
            
            # Clean up quotes if present
            if val_str.startswith("'") and val_str.endswith("'"):
                val_str = val_str[1:-1]
            elif val_str.startswith('"') and val_str.endswith('"'):
                val_str = val_str[1:-1]
                
            # Handle list-like syntax for in/equals
            if val_str.startswith("[") and val_str.endswith("]"):
                try:
                    values = ast.literal_eval(val_str)
                    if not isinstance(values, list):
                        values = [values]
                except Exception:
                    values = [v.strip() for v in val_str[1:-1].split(",")]
            else:
                values = [val_str]
                
            return {
                "member": member,
                "operator": op_name,
                "values": values
            }
            
    return None


def normalize_filter(f: dict) -> dict:
    normalized = {}
    
    # 1. Map member/dimension/field/column
    member = f.get("member") or f.get("dimension") or f.get("field") or f.get("column")
    
    # Robust fallback: check if any key contains a dot (e.g. 'cube.field')
    if not member:
        for k in f.keys():
            if isinstance(k, str) and "." in k and k not in ("operator", "values", "value", "member", "dimension", "field", "column"):
                member = k
                break
                
    if member:
        normalized["member"] = resolve_member(str(member))
        
    # 2. Map operator — normalize aliases and reject unknowns
    operator = str(f.get("operator") or "equals").strip()
    operator = _OPERATOR_ALIASES.get(operator.lower(), operator)
    if operator not in _VALID_CUBE_OPERATORS:
        operator = "equals"
    normalized["operator"] = operator
    
    # 3. Map values
    raw_values = f.get("values")
    if raw_values is None:
        raw_values = f.get("value")
        
    # Use the value of the member key if values was not explicitly set
    if raw_values is None and member in f:
        raw_values = f[member]
        
    # Standardize values to a list of strings
    if raw_values is None:
        values_list = []
    elif isinstance(raw_values, list):
        values_list = [str(v) for v in raw_values]
    elif isinstance(raw_values, str):
        # Handle range strings for date operators
        if operator in ("inDateRange", "onDateRange") or "date" in str(member).lower():
            rv_lower = raw_values.lower()
            if " to " in rv_lower:
                values_list = [v.strip() for v in re.split(r"(?i) to ", raw_values)]
            elif " and " in rv_lower:
                values_list = [v.strip() for v in re.split(r"(?i) and ", raw_values)]
            elif "," in raw_values:
                values_list = [v.strip() for v in raw_values.split(",")]
            else:
                values_list = [raw_values]
        else:
            # Handle comma-separated values for other operators if it looks like a list
            if "," in raw_values and operator in ("equals", "notEquals"):
                values_list = [v.strip() for v in raw_values.split(",")]
            else:
                values_list = [raw_values]
    else:
        values_list = [str(raw_values)]
        
    normalized["values"] = values_list
    return normalized


def extract_date_range_from_dict(d: dict) -> list | None:
    if not isinstance(d, dict):
        return None
        
    start = (
        d.get("start") or d.get("from") or
        d.get("startInstant") or d.get("startDate") or d.get("start_date")
    )
    end = (
        d.get("end") or d.get("to") or
        d.get("endInstant") or d.get("endDate") or d.get("end_date")
    )

    if start and end:
        # Strip trailing time component so CubeJS receives a plain date string
        return [str(start).split("T")[0], str(end).split("T")[0]]

    for k, v in d.items():
        if isinstance(v, dict):
            res = extract_date_range_from_dict(v)
            if res:
                return res

    return None


def normalize_time_dimension(td: dict) -> dict | None:
    if not isinstance(td, dict):
        return None

    # Eagerly scan the whole td for any nested date-range data before touching
    # the dimension field, so we don't lose it when the LLM mixes date objects
    # and dimension names.
    extracted_date_range: list | None = None
    for v in td.values():
        if isinstance(v, dict):
            dr = extract_date_range_from_dict(v)
            if dr:
                extracted_date_range = dr
                break

    # Find the dimension key — skip any value that is itself a dict (date object)
    dimension = None
    for key in ("dimension", "member", "field", "column"):
        val = td.get(key)
        if val and not isinstance(val, dict):
            dimension = val
            break

    if not dimension:
        # Robust fallback: find a string key that looks like a schema member
        for k in td.keys():
            if (
                isinstance(k, str)
                and (k in SCHEMA_MAPPING or "." in k)
                and k not in ("granularity", "dateRange", "values", "value")
            ):
                dimension = k
                break

    # Fallback to reg_date if no dimension found
    if not dimension:
        dimension = "fct_horasreportadas.reg_date"

    resolved_dim = resolve_member(str(dimension))

    # If the resolved dimension is not a time dimension, use reg_date
    if "date" not in resolved_dim.lower():
        resolved_dim = "fct_horasreportadas.reg_date"

    # Final guard: dimension must match CubeJS Cube.field pattern
    if not _MEMBER_PATTERN.match(resolved_dim):
        logger.warning(f"Skipping timeDimension with invalid dimension: {resolved_dim!r}")
        return None

    normalized: dict = {
        "dimension": resolved_dim,
        "granularity": str(td.get("granularity") or "month"),
    }

    # Map dateRange
    date_range = td.get("dateRange") or td.get("values") or td.get("value")
    if date_range is None:
        if extracted_date_range:
            date_range = extracted_date_range
        elif dimension in td:
            val = td[dimension]
            if isinstance(val, dict):
                date_range = extract_date_range_from_dict(val)
            else:
                date_range = val

    if date_range:
        if isinstance(date_range, list):
            normalized["dateRange"] = [str(d) for d in date_range]
        elif isinstance(date_range, str):
            dr_lower = date_range.lower()
            if " to " in dr_lower:
                normalized["dateRange"] = [d.strip() for d in re.split(r"(?i) to ", date_range)]
            elif " and " in dr_lower:
                normalized["dateRange"] = [d.strip() for d in re.split(r"(?i) and ", date_range)]
            elif "," in date_range:
                normalized["dateRange"] = [d.strip() for d in date_range.split(",")]
            else:
                normalized["dateRange"] = [date_range]

    return normalized


def normalize_order(order, query: dict):
    """
    Normalizes the sorting order parameter, resolving custom attributes to physical keys.
    Also handles resolving 'dimensions'/'measures' placeholders to the active query elements
    to prevent LLM query syntax errors.
    """
    if not order:
        return order

    def resolve_order_member(m: str) -> str:
        m_stripped = str(m).strip()
        m_lower = m_stripped.lower()
        if m_lower in ("dimensions", "dimension"):
            dims = query.get("dimensions")
            if dims and isinstance(dims, list) and len(dims) > 0:
                return dims[0]
        elif m_lower in ("measures", "measure"):
            meas = query.get("measures")
            if meas and isinstance(meas, list) and len(meas) > 0:
                return meas[0]
        return resolve_member(m_stripped)

    # 1. Dict format: e.g. {"jornada": "desc"}
    if isinstance(order, dict):
        return {resolve_order_member(k): v for k, v in order.items()}

    # 2. List format: e.g. [["jornada", "desc"]] or [{"id": "jornada", "desc": True}]
    if isinstance(order, list):
        new_order = []
        for item in order:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                new_order.append([resolve_order_member(item[0]), item[1]])
            elif isinstance(item, dict):
                new_item = {}
                for k, v in item.items():
                    if k == "id":
                        new_item["id"] = resolve_order_member(v)
                    else:
                        new_item[k] = v
                new_order.append(new_item)
            elif isinstance(item, str):
                parts = item.strip().split()
                if len(parts) >= 2:
                    new_order.append(f"{resolve_order_member(parts[0])} {parts[1]}")
                else:
                    new_order.append(resolve_order_member(item))
            else:
                new_order.append(item)
        return new_order

    # 3. String format: e.g. "jornada desc" or "jornada"
    if isinstance(order, str):
        parts = order.strip().split()
        if len(parts) >= 2:
            return f"{resolve_order_member(parts[0])} {parts[1]}"
        return resolve_order_member(order)

    return order


async def query_data(
    query: dict | None = None,
    measures: list | str | None = None,
    dimensions: list | str | None = None,
    timeDimensions: list | dict | None = None,
    filters: list | dict | None = None,
    limit: int | str | None = None,
    offset: int | str | None = None,
    order: dict | list | str | None = None,
):
    """
    Fetches business data from CubeJS using the provided JSON query format.
    
    Use this tool to explore data beyond the current screen context or to get
    detailed metrics and dimensions from the database.
    
    You can either pass the entire query object in the 'query' argument, OR
    pass the individual query properties (measures, dimensions, filters, etc.)
    directly as top-level arguments.
    
    Example queries (as direct arguments):
    - Total hours and cost: measures=["fct_horasreportadas.total_hours", "fct_horasreportadas.cost"]
    - Hours by product: measures=["fct_horasreportadas.total_hours"], dimensions=["fct_horasreportadas.product"]
    
    Args:
        query (dict): Optional. A complete CubeJS JSON query object.
        measures (list or str): Optional. The list of measures or single measure, e.g. ["fct_horasreportadas.total_hours"]
        dimensions (list or str): Optional. The list of dimensions or single dimension, e.g. ["fct_horasreportadas.product"]
        timeDimensions (list or dict): Optional. Time dimensions config.
        filters (list or dict): Optional. Filter conditions (can be a list of filters or a single filter object).
        limit (int or str): Optional. Max number of rows to return.
        offset (int or str): Optional. Number of rows to skip.
        order (dict or list or str): Optional. Ordering configuration.
        
    Returns:
        list: The 'data' array from CubeJS response.
    """
    if query is None:
        query = {}
        if measures is not None:
            query["measures"] = _parse_list_arg(measures)
        if dimensions is not None:
            query["dimensions"] = _parse_list_arg(dimensions)
        if timeDimensions is not None:
            query["timeDimensions"] = [timeDimensions] if isinstance(timeDimensions, dict) else timeDimensions
        if filters is not None:
            if isinstance(filters, list):
                query["filters"] = filters
            else:
                query["filters"] = [filters]
        if limit is not None and str(limit).strip().lower() not in ("none", "", "null"):
            query["limit"] = int(limit) if isinstance(limit, str) else limit
        if offset is not None and str(offset).strip().lower() not in ("none", "", "null"):
            query["offset"] = int(offset) if isinstance(offset, str) else offset
        if order is not None:
            query["order"] = order
    else:
        # Standardize nested query fields if they were passed inside the 'query' object
        if "measures" in query and isinstance(query["measures"], str):
            query["measures"] = [query["measures"]]
        if "dimensions" in query and isinstance(query["dimensions"], str):
            query["dimensions"] = [query["dimensions"]]
        if "timeDimensions" in query and isinstance(query["timeDimensions"], dict):
            query["timeDimensions"] = [query["timeDimensions"]]
        if "filters" in query and not isinstance(query["filters"], list):
            query["filters"] = [query["filters"]] if query["filters"] is not None else []
        if "limit" in query and isinstance(query["limit"], str):
            if query["limit"].strip().lower() not in ("none", "", "null"):
                query["limit"] = int(query["limit"])
            else:
                del query["limit"]
        if "offset" in query and isinstance(query["offset"], str):
            if query["offset"].strip().lower() not in ("none", "", "null"):
                query["offset"] = int(query["offset"])
            else:
                del query["offset"]

    # Merge active dashboard filters into the query
    if _active_filters:
        existing = query.get("filters", [])
        if isinstance(existing, list):
            query = {**query, "filters": existing + _active_filters}
        else:
            query = {**query, "filters": ([existing] if existing else []) + _active_filters}

    # Normalize final filters list to conform strictly to CubeJS specification
    if "filters" in query:
        raw_filters = query["filters"]
        if not isinstance(raw_filters, list):
            raw_filters = [raw_filters] if raw_filters is not None else []
            
        seen = set()
        normalized_filters = []
        expanded: list = []
        for f in raw_filters:
            if isinstance(f, str):
                stripped = f.strip()
                # Try to decode JSON/literal-encoded filter objects or lists
                if stripped.startswith("{"):
                    try:
                        f = json.loads(stripped)
                    except Exception:
                        try:
                            f = ast.literal_eval(stripped)
                        except Exception:
                            f = parse_string_filter(f)
                elif stripped.startswith("["):
                    try:
                        parsed = ast.literal_eval(stripped)
                        if isinstance(parsed, list):
                            expanded.extend(parsed)
                            continue
                    except Exception:
                        pass
                    f = parse_string_filter(f)
                else:
                    f = parse_string_filter(f)
            if isinstance(f, dict):
                norm = normalize_filter(f)
                if "member" not in norm:
                    continue
                # Reject members that don't match CubeJS Cube.field pattern
                if not _MEMBER_PATTERN.match(norm["member"]):
                    logger.warning(f"Skipping filter with invalid member: {norm['member']!r}")
                    continue
                # Skip filters with no values for value-requiring operators
                if norm["operator"] in ("equals", "notEquals", "contains", "notContains", "gt", "gte", "lt", "lte") and not norm["values"]:
                    continue
                values_tuple = tuple(sorted(norm["values"]))
                key = (norm["member"], norm["operator"], values_tuple)
                if key not in seen:
                    seen.add(key)
                    normalized_filters.append(norm)
        # Process any filters that were expanded from a string-encoded list
        for f in expanded:
            if isinstance(f, dict):
                norm = normalize_filter(f)
                if "member" not in norm or not _MEMBER_PATTERN.match(norm["member"]):
                    continue
                if norm["operator"] in ("equals", "notEquals", "contains", "notContains", "gt", "gte", "lt", "lte") and not norm["values"]:
                    continue
                values_tuple = tuple(sorted(norm["values"]))
                key = (norm["member"], norm["operator"], values_tuple)
                if key not in seen:
                    seen.add(key)
                    normalized_filters.append(norm)
        query["filters"] = normalized_filters

    # Normalize measures
    if "measures" in query:
        query["measures"] = [resolve_member(m) for m in _parse_list_arg(query["measures"]) if m]

    # Normalize dimensions
    if "dimensions" in query:
        query["dimensions"] = [resolve_member(d) for d in _parse_list_arg(query["dimensions"]) if d]

    # Normalize order
    if "order" in query:
        query["order"] = normalize_order(query["order"], query)

    # Normalize timeDimensions
    if "timeDimensions" in query:
        raw_tds = query["timeDimensions"]
        if not isinstance(raw_tds, list):
            raw_tds = [raw_tds] if raw_tds is not None else []
            
        normalized_tds = []
        for td in raw_tds:
            if isinstance(td, str):
                td = {"dimension": td}
            if isinstance(td, dict):
                norm = normalize_time_dimension(td)
                if norm:
                    normalized_tds.append(norm)
        query["timeDimensions"] = normalized_tds

    payload = {
        "sub": "ai-analyst",
        "iat": int(time.time()),
        "exp": int(time.time()) + (1 * 60 * 60)  # 1 hour
    }
    
    token = jwt.encode(payload, settings.cubejs_api_secret, algorithm="HS256")
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Querying CubeJS at {settings.cubejs_url} with query: {query}")
            response = await client.post(
                settings.cubejs_url,
                json={"query": query},
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                logger.error(f"CubeJS error in response: {result['error']}")
                return f"CubeJS error: {result['error']}"
                
            return result.get("data", [])
            
        except httpx.HTTPStatusError as e:
            logger.error(f"CubeJS HTTP error: {e.response.status_code} - {e.response.text}")
            return f"Error querying data: {e.response.text}"
        except Exception as e:
            logger.error(f"CubeJS unexpected error: {str(e)}")
            return f"Error querying data: {str(e)}"
