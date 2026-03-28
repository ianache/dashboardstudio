# Objetivo

Crear un nuevo menu en el dashboard llamado "Models" que permita gestionar diferentes "Dimensional Models" basados en "Facts y Dimensiones".

Necesito planificar el desarrollo de un nuevo feature para diseñadores que permita "Gestionar modelos dimensionales basados en facts and dimensions".

# Requerimientos

1. Añadir al menu principal debajo de "DISEÑO" un submenu "Models" equivalene a "Mis dashboards" pero que me permita
gestionar diferentes "Dimensional Models" basados en "Facts y Dimensiones". 
2. Añadir una opción "Ver Todos" y "Nuevo Modelo". 
3. Al seleccionar "Ver Todos" debe mostrar tarjetas para cada modelo dimensional creado similar a las tarjeras de los "Dashboards"
4. Al seleccionar "Nuevo Modelo" debe mostrar un lienzo para el editiar en forma de diagrama de entidades y relaciones como Modelador de Datos dimensional.
5. El modelo dimensional debe tener las siguientes propiedades:
    - Nombre
    - Descripción
    - Diagrama de datos con los hechos, dimensiones y relaciones entre ellos.
6. Al seleccionar un hecho o dimensión se debe mostrar un formulario para configurar sus propiedades.
7. Al seleccionar un hecho se debe mostrar un formulario para configurar sus propiedades.
8. Al seleccionar una dimensión se debe mostrar un formulario para configurar sus propiedades.
9. Al seleccionar una relación se debe mostrar un formulario para configurar sus propiedades.
10. El formulario de la tabla de hechos debe permitir añadir todas las metricas (nombre, descripcion, tipo de datos numerico.
11. El formulario de la tabla de dimensiones debe permitir añadir todas los atributos cualitativos (nombre, descripcion, tipo de datos texto, fecha, etc).
12. El formulario de la relación debe permitir configurar las multiplicidades de la relación (uno a uno, uno a muchos, muchos a muchos).

# Mejoras

- necesito poder exportar (icono a la izquierda de "+ Hecho" o importar con icono a la izquierda de exportar) en formato yaml con estructura estandarizada. El nombre del archivo al exportar debe ser el nombre del modelo dimensional.
- Necesito que al añadir una relacion se arrastre de una tabla de dimensiones (dim) el campo marcado como llave y al soltarla sobre la tabla de hechos lo vincule con un atributo para relacion en la tabla de fact (si existe un atributo de relacion) o añada automaticamente el campo en la tabla de fact siguiendo el patron "nombre-table-dim_nombre-campo-llave). En la tabla de dimensiones siempre se debe marcar un atributo como llave.
- Necesito que en el card de cada modelo se pueda editar en linea a simple click sobre titulo y descripcion.
- Necesito poder generar completamente el codigo SQL/DDL (icono a la izquierda de importar) de todo el modelo dimensional. El nombre del archivo debe ser el nombre del modelo con extension ".ddl"