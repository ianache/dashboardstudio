# Goal

# Requirements

- Se requiere un visualizar gráfico que muestre el diagrama de flujo del integration mostrando con badge en la parte izquier superior del nodo indicando "tiempo de ejecución" del nodo y otro badge en la parte derecha superior del nodo indicando si fue exitoso (check verde) o fallido (cruz roja). Al realizar un hover sobre el nodo se debe mostrar una ficha que muestre fecha y hora de inicio, fecha y hora fin. Este visualizador debe ser un componente reutilizable que aparezca a modo de popup cuando se seleccione en la pagina "integrations" el icon "lupa" en la columna "ACCIONES" para cada fila de la tabla de integration

- Se requiere visualizar el gráfico como componente estandar (FlowEditorCanvas) cuando se seleccone una ejecución del historial de ejecuciones colocando un icono de lupa en la columna "ACCIONES" para cada fila de la tabla de ejecuciones. Modificar el boton actual "Ver" por un icono que represente "details".

- El nodo 'ODS PostgreSQL' debe permitir realizar el upsert, considerando uno o varios campos en la tabla destino seleccionados (solo cuando el modo de escritura sea UPSERT) como los campos de identidad identidad/llave primaria (simple o combinada). El editor de propiedades debiera permitir listar las tablas para el esquema (al costado del editor de 'TABLA DESTINO' que deberá ser un combobox de edición y selección unica) debe colocarse un boton para Refresh que deberá obtener todas las tablas disponibles