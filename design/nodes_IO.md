# Especificación de Entradas y Salidas de Nodos (I/O) & Estructura del Contexto

Este documento describe con precisión la arquitectura de datos, la estructura del objeto de contexto global (`context`) y las especificaciones de entrada/salida (I/O) para todos los nodos del motor de ejecución de Dashboard Studio (Deno Runtime Engine).

---

## 1. El Objeto de Contexto Global (`context`)

En la raíz del motor de integraciones, cada flujo opera sobre un estado de datos compartido que se transfiere secuencialmente a lo largo del orden topológico. Este objeto se estructura de la siguiente manera:

```typescript
interface GlobalContext {
  payload: any;             // Mensaje activo, payload de datos o resultado del último nodo ejecutado
  variables: Record<string, any>; // Variables globales compartidas por el flujo
}
```

* **`payload`**: Representa la información fluyendo de un nodo a otro. Puede ser un arreglo puro, un objeto JSON estructurado, un texto plano o vacío (`null`).
* **`variables`**: Diccionario mutable de pares clave-valor que persiste a lo largo de toda la vida del flujo y que los scripts u otros nodos pueden consultar o actualizar.

---

## 2. El Contexto de Bifurcación (`branchContext`) de Fragmentación

Cuando el motor entra en un bloque de ejecución fragmentado por un par **DSplit / DJoin**, el contexto global se clona localmente para cada fragmento, inyectando metadatos críticos de control en la propiedad `split`:

```typescript
interface BranchContext {
  payload: any;             // El elemento individual correspondiente a este fragmento
  variables: Record<string, any>; // Copia de variables globales del flujo
  split: {
    fragment_index: number;   // Índice del fragmento (0-indexed)
    total_fragments: number;  // Cantidad total de fragmentos generados
    dsplit_node_id: string;   // ID único del nodo DSplit originador
  }
}
```

> [!NOTE]
> La propiedad `split` sirve para que los nodos internos (como **JS Script**) e instrumentadores (como **DJoin**) validen la procedencia, contabilicen los fragmentos procesados y determinen si se ha recibido el último fragmento para dar fin a la agregación.

---

## 3. Especificación de I/O por Tipo de Nodo

### A. DSplit (`dsplit`)
Nodo de fragmentación topológica de bucles. Toma una lista y ejecuta de forma asíncrona (paralela o serie) un sub-diagrama por cada elemento.

* **Estructura del Input Payload:**
  Soporta múltiples formatos de entrada:
  1. Arreglo plano (ej. `[ { "id": 1 }, { "id": 2 } ]`).
  2. Objeto con atributo `payload` que contenga el arreglo (ej. `{ "payload": [ ... ] }`).
  3. Objeto con atributo `data` que contenga el arreglo (ej. `{ "data": [ ... ] }`).
* **Estructura del Output Payload (para cada rama):**
  * `item`: Cada registro/elemento individual del arreglo original.
* **Estructura del Registro del Historial de Ejecución:**
  * **Input**: El arreglo original (o el objeto envoltorio).
  * **Output**: El elemento individual correspondiente a la rama actual (`item`).

---

### B. DJoin (`djoin`)
Nodo de consolidación y cierre de bucles. Sincroniza y recoge los flujos resultantes de cada rama de DSplit para integrarlos.

* **Estructura del Input Payload:**
  * Una lista (`djoinOutputs`) que recopila los payloads del último nodo de cada rama del sub-diagrama.
* **Estructura del Output Payload:**
  * Un arreglo plano que unifica y aplana los payloads individuales de cada rama usando `.flat()`:
    ```json
    [
      { "id": 65, "result": "procesado_1" },
      { "id": 63, "result": "procesado_2" }
    ]
    ```

---

### C. Custom JS Script (`js_script`)
Bloque programable en Javascript/Typescript.

* **Estructura del Input Payload:**
  * Recibe el `context` completo en su función por defecto (`export default async function(ctx)`). Puede leer `ctx.payload` y `ctx.variables`.
* **Estructura del Output Payload:**
  * El valor de retorno de la función del script. Sobrescribe automáticamente el `ctx.payload` para los nodos aguas abajo.

* **Ejemplo de Código Interno:**
  ```javascript
  export default async function(ctx) {
    const data = ctx.payload; // Recibe un fragmento si está en DSplit
    return {
      ...data,
      processed_at: new Date().toISOString(),
      index: ctx.split?.fragment_index ?? null
    };
  }
  ```

---

### D. HTTP REST / GraphQL API (`http_rest`, `graphql_api`)
Permite invocar servicios Web RESTful o GraphQL.

* **Estructura del Input Payload:**
  * El payload activo (`context.payload`). Opcionalmente se puede inyectar y formatear dinámicamente mediante plantillas en los Headers, Query Params o Body.
* **Estructura del Output Payload:**
  * Un objeto JSON que mapea la respuesta del servidor (o texto plano si la respuesta no es serializable como JSON).
    ```json
    {
      "status": 200,
      "data": { ... }
    }
    ```

---

### E. SQL Source / Destination (`sql_source`, `sql_destination`)
Consultas directas a motores de base de datos relacionales (PostgreSQL, MySQL, SQL Server, etc.).

* **Estructura del Input Payload:**
  * `context.payload` y variables globales interpolables dentro de la sentencia SQL parametrizada.
* **Estructura del Output Payload:**
  * Un arreglo de objetos, donde cada objeto representa una fila de la base de datos consultada:
    ```json
    [
      { "columna1": "valor1", "columna2": 123 },
      { "columna1": "valor2", "columna2": 456 }
    ]
    ```

---

### F. Join (`join` estándar)
Combina o recolecta payloads que provienen de múltiples ramas topológicas convergentes que no forman parte de un bucle DSplit.

* **Estructura del Input Payload:**
  * Un arreglo conteniendo los payloads resultantes de cada una de las conexiones entrantes al nodo Join.
* **Estructura del Output Payload:**
  * El arreglo unificado de entradas combinadas.

---

### G. CSV File (`csv_file`)
Lectura o escritura física de archivos en formato delimitado por comas.

* **Estructura del Input Payload:**
  * **Lectura:** No requiere payload previo (lee del sistema de archivos).
  * **Escritura:** Un arreglo de objetos JSON para ser convertidos a filas CSV.
* **Estructura del Output Payload:**
  * **Lectura:** Un arreglo de objetos JSON correspondientes a las filas del archivo CSV.
  * **Escritura:** Un objeto de metadatos indicando el estado del archivo escrito.

---

### H. Email (`email`)
Envío automatizado de correos electrónicos vía SMTP.

* **Estructura del Input Payload:**
  * Datos dinámicos desde `context.payload` para rellenar plantillas HTML o destinatarios.
* **Estructura del Output Payload:**
  * Un objeto indicando el resultado del envío:
    ```json
    { "sent": true, "messageId": "<...>" }
    ```

---

### I. ODS Postgres (`ods_pg`)
Operaciones y transacciones de alta velocidad integradas con el ODS local.

* **Estructura del Input Payload:**
  * Los parámetros de la transacción o registros origen estructurados.
* **Estructura del Output Payload:**
  * Las filas y metadatos resultantes de las operaciones transaccionales consolidadas.
