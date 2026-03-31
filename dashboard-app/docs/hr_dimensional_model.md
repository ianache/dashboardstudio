# Modelo Dimensional: Recursos Humanos (HR)

Este documento define la estructura de hechos (Facts) y dimensiones (Dimensions) para un esquema en estrella orientado a la gestión y análisis de KPIs clave en Recursos Humanos.

## Contexto del Modelo
- **Nombre:** Recurso Humano
- **Descripción:** Modelo dimensional para analizar la fuerza laboral, retención, ausentismo, salarios y el embudo de reclutamiento de la empresa.

---

## 📅 Dimensiones (Dimensions)

Las dimensiones proporcionan el contexto para filtrar, agrupar y analizar los hechos.

### 1. `dim_empleado`
Contiene la información demográfica y descriptiva de los colaboradores.
- `id_empleado` (🔑 PK)
- `dni` (VARCHAR)
- `nombre_completo` (VARCHAR)
- `genero` (VARCHAR)
- `fecha_nacimiento` (DATE)
- `estado_civil` (VARCHAR)
- `nivel_educativo` (VARCHAR)

### 2. `dim_departamento`
Estructura organizacional de la empresa.
- `id_departamento` (🔑 PK)
- `nombre_departamento` (VARCHAR)
- `area` (VARCHAR)
- `director_departamento` (VARCHAR)

### 3. `dim_rol`
Posiciones y roles organizacionales.
- `id_rol` (🔑 PK)
- `titulo_puesto` (VARCHAR)
- `nivel_seniority` (VARCHAR) - Ej. Junior, Semi-Senior, Senior
- `familia_puestos` (VARCHAR)

### 4. `dim_tiempo`
Dimensión estándar de fechas.
- `id_tiempo` (🔑 PK)
- `fecha` (DATE)
- `año` (INTEGER)
- `trimestre` (INTEGER)
- `mes` (INTEGER)
- `dia_semana` (VARCHAR)

---

## 📊 Tablas de Hechos (Facts)

Los hechos contienen las métricas (métricas cuantitativas) y las llaves foráneas a las dimensiones.

### 1. `fact_headcount_mensual` (Snapshot Mensual)
Mide la cantidad de empleados activos, salarios y retención al cierre de cada mes.
**Campos:**
- `id_tiempo` (🔗 FK -> dim_tiempo)
- `id_empleado` (🔗 FK -> dim_empleado)
- `id_departamento` (🔗 FK -> dim_departamento)
- `id_rol` (🔗 FK -> dim_rol)
- `salario_base` (NUMERIC)
- `bonos` (NUMERIC)
- `es_activo` (BOOLEAN) - Para contar Headcount
- `es_nueva_contratacion` (BOOLEAN)

### 2. `fact_ausentismo`
Registra cada evento de ausencia (vacaciones, enfermedad, faltas injustificadas).
**Campos:**
- `id_ausencia` (🔑 PK)
- `id_tiempo_inicio` (🔗 FK -> dim_tiempo)
- `id_empleado` (🔗 FK -> dim_empleado)
- `id_departamento` (🔗 FK -> dim_departamento)
- `tipo_ausencia` (VARCHAR) - Ej. Vacaciones, Médica, Injustificada
- `dias_ausencia` (NUMERIC)
- `horas_ausencia` (NUMERIC)

### 3. `fact_reclutamiento`
Mide la eficiencia del proceso de contratación y embudo de talento.
**Campos:**
- `id_candidatura` (🔑 PK)
- `id_tiempo_aplicacion` (🔗 FK -> dim_tiempo)
- `id_departamento` (🔗 FK -> dim_departamento)
- `id_rol` (🔗 FK -> dim_rol)
- `origen_candidato` (VARCHAR) - Ej. LinkedIn, Referido, Web
- `dias_para_contratar` (INTEGER) - Time-to-hire
- `estado_embudo` (VARCHAR) - Ej. Entrevista, Oferta, Contratado, Rechazado
- `costo_contratacion` (NUMERIC)
