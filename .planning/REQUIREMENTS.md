# Requirements: Flow Execution Visualization

## 1. Functional Requirements

### FR-01: Backend Status Reporting
- El `runner.ts` debe emitir mensajes de estado para cada nodo durante la ejecución: `NODE_STATUS:<node_id>:<status>`.
- Los estados soportados son: `running`, `success`, `error`.
- El `DenoService` debe capturar estos mensajes y emitirlos como eventos estructurados vía WebSocket: `{"type": "node_status", "node_id": "...", "status": "..."}`.

### FR-02: Real-time Node Border Highlighting
- Cuando un nodo recibe el estado `running`, debe mostrar un borde verde grueso (ej: `3px solid #22c55e`).
- Al terminar la ejecución del nodo, el borde debe volver a la normalidad o cambiar según su resultado final.

### FR-03: Execution Status Badges
- Al finalizar la ejecución de un nodo con éxito, se debe mostrar un badge de "check" verde en la esquina superior derecha del nodo.
- Si la ejecución falla, se debe mostrar un badge de "cross" roja.

### FR-04: Connection Sequence Visualization
- Al finalizar un nodo con éxito, todas las conexiones que parten de ese nodo (hacia adelante) deben cambiar su color a verde (ej: `#22c55e`) y posiblemente aumentar su grosor.
- Esto indica visualmente que esa parte del flujo ha sido "activada" y completada.

### FR-05: Execution State Management
- El frontend debe mantener un estado reactivo de la ejecución actual (mapeo de `node_id` -> `status`).
- Este estado debe limpiarse al iniciar una nueva ejecución.

## 2. Technical Requirements

### TR-01: WebSocket Event Expansion
- El esquema de mensajes de WebSocket debe ampliarse para incluir el tipo `node_status`.

### TR-02: CSS Dynamic Classes
- Implementar clases CSS en `FlowEditorCanvas.vue` para los estados de ejecución de nodos y conexiones.

### TR-03: Node Badge Components
- Añadir elementos visuales (iconos de Material Symbols) dentro del componente de nodo en el canvas para los badges.

## 3. Success Criteria
- [ ] Al ejecutar un flujo, se ve claramente qué nodo está corriendo actualmente.
- [ ] Las flechas se vuelven verdes secuencialmente según avanza la ejecución.
- [ ] Los nodos terminan con un icono de éxito o error.
- [x] La visualización es fluida y sincronizada con los logs de la consola.

# Requirements: Connection Management & Centralized Credentials

## 1. Functional Requirements

### FR-06: Centralized Connection Store
- Permitir la creación de conexiones reutilizables que puedan ser referenciadas por los nodos del Flow Editor.
- Cada conexión debe tener un nombre único y un tipo.

### FR-07: Polymorphic Connection Configurations
- Soportar configuraciones específicas según el tipo:
    - **Email (SMTP):** host, port, use_ssl, email, password.
    - **Database:** host, port, username, password, database, schema.
    - **FTP:** host, port, username, password, protocol, schema.
    - **HTTP:** url, username, password.
    - **JWT:** token_url, username, password, client_id, client_secret, grant_type.

### FR-08: Connection Testing
- Implementar una funcionalidad de "Test Connection" en la UI que verifique la conectividad y credenciales según el tipo de conexión.

### FR-09: Connection Management UI
- Vista de listado de conexiones con búsqueda y filtrado por tipo.
- Formulario dinámico para añadir/editar conexiones basado en el tipo seleccionado.
- Opción para eliminar conexiones (validando si están en uso).

### FR-10: Submenu Integration
- Añadir el ítem "Conexiones" bajo el menú "DATA INTEGRATION" en el SideMenu.

## 2. Technical Requirements

### TR-04: Polymorphic Data Model (JSON Config)
- Extender el modelo `DataSource` con un campo JSON `connection_config` para almacenar las propiedades granulares.
- Implementar validación con Pydantic Discriminated Unions en los esquemas de la API.

### TR-05: Recursive Encryption Helper
- Implementar un helper en el backend que encripte/desencripte recursivamente campos sensibles (`password`, `client_secret`, `token`) dentro del JSON de configuración.

### TR-06: Connection Strategy Pattern
- Implementar una clase base de estrategia y subclases por protocolo para encapsular la lógica de test de conexión.

## 3. Success Criteria
- [ ] El usuario puede crear una conexión SMTP y verificar que los datos son correctos mediante un test.
- [ ] Las contraseñas se almacenan encriptadas en la base de datos (incluso dentro del JSON).
- [ ] El SideMenu muestra el nuevo acceso a "Conexiones".
- [ ] La UI se adapta dinámicamente según el tipo de conexión seleccionado.
