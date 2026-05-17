# Guía de Configuración de Plantillas para el Nodo EMail

Esta guía describe cómo configurar de forma óptima el **Asunto (Subject)** y el **Cuerpo (Body)** del nodo **EMail** utilizando la sintaxis de plantillas **Jinja2**.

---

## 1. Sintaxis Básica de Jinja2

Para evitar errores en la compilación de tus correos, recuerda la diferencia entre las dos etiquetas principales:

* **`{{ ... }}` (Doble Llave):** Se utiliza para **imprimir o referenciar variables**.
  * *Ejemplo:* `{{ text }}`, `{{ records|length }}`
* **`{% ... %}` (Llave y Porcentaje):** Se utiliza exclusivamente para **estructuras de control lógico** (bucles, condicionales).
  * *Ejemplo:* `{% if status == 'success' %}`, `{% for row in records %}`

> [!WARNING]
> **Error Común:** Escribir `{% text %}` arrojará un error `Encountered unknown tag 'text'`. Asegúrate de usar siempre `{{ text }}` para imprimir variables.

---

## 2. Caso 1: Integración con Nodo "JS Script" (Mensajes de Texto Preformateados)

Cuando usas un nodo **JS Script** previo para procesar la información y construir un string listo para enviar (como notificaciones de estado), tu flujo se configura de la siguiente manera:

### Código en el Nodo "JS Script"
El nodo de JS debe retornar un objeto con el mensaje. Por ejemplo:
```javascript
export default async function(ctx) {
  const { payload } = ctx;

  let registros = Array.isArray(payload) ? payload : Object.values(payload || {});
  const totalRegistros = registros.length;

  const textoMensaje = `📊 *Notificación de Sincronización*\n` +
    `• Estado: *Exitoso*\n` +
    `• Total de registros procesados: *${totalRegistros}* unidades.\n` +
    `• Fecha/Hora: _${new Date().toLocaleString('es-PE')}_`;

  return { text: textoMensaje };
}
```

### Configuración del Nodo EMail

#### A. Asunto (Subject)
```text
Sincronización Exitosa - Ejecución {{ execution_id[:8] }}
```

#### B. Cuerpo (Body) en Modo **Plain Text (Texto Plano)**
Si configuras el nodo para enviar texto plano, se respetarán todos los saltos de línea (`\n`) automáticamente:
```text
{{ text }}
```

#### C. Cuerpo (Body) en Modo **HTML**
Si prefieres enviar un correo con formato HTML moderno, debes reemplazar los saltos de línea (`\n`) por tags `<br>` y usar el filtro `safe` para indicarle al motor que renderice el HTML seguro:
```html
<div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
  <div style="font-size: 16px; font-weight: bold; color: #1a365d; margin-bottom: 12px;">
    DashboardStudio - Telemetría e Integraciones
  </div>
  <div style="background-color: #f7fafc; padding: 15px; border-radius: 6px; border-left: 4px solid #3182ce;">
    {{ text | replace('\n', '<br>') | safe }}
  </div>
</div>
```

---

## 3. Caso 2: Reporte de Tabla Dinámica (Datos Directos de Base de Datos / ODS)

Cuando conectas el nodo de correo directamente a un nodo que devuelve una **lista de registros** (como ODS PostgreSQL o Source SQL), DashboardStudio los expone en la variable **`records`** para crear tablas HTML avanzadas de forma dinámica.

### Configuración del Nodo EMail (Modo HTML)

#### A. Asunto (Subject)
```text
[Reporte] {{ records|length }} Registros Procesados
```

#### B. Cuerpo (Body)
```html
<div style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; color: #2d3748; max-width: 600px; margin: 0 auto; border: 1px solid #edf2f7; border-radius: 8px; overflow: hidden;">
  <!-- Header -->
  <div style="background: linear-gradient(135deg, #2b6cb0, #1a365d); color: #ffffff; padding: 20px; text-align: center;">
    <h2 style="margin: 0; font-size: 20px;">Sincronización de Calendario</h2>
  </div>
  
  <!-- Content -->
  <div style="padding: 20px; background-color: #ffffff;">
    <p>Detalle de la sincronización correspondiente a la ejecución <strong>{{ execution_id }}</strong>:</p>
    
    <!-- Dynamic Table -->
    <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px;">
      <thead>
        <tr style="background-color: #edf2f7; color: #4a5568; text-align: left;">
          <th style="padding: 8px; border-bottom: 2px solid #cbd5e0;">Día</th>
          <th style="padding: 8px; border-bottom: 2px solid #cbd5e0;">Nro. Día</th>
          <th style="padding: 8px; border-bottom: 2px solid #cbd5e0; text-align: right;">Horas</th>
        </tr>
      </thead>
      <tbody>
        {% for row in records %}
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 8px; font-weight: 500; color: #2b6cb0;">{{ row.dia }}</td>
          <td style="padding: 8px; color: #718096;">{{ row.nrodia }}</td>
          <td style="padding: 8px; text-align: right;">{{ row.horas }} hrs</td>
        </tr>
        {% else %}
        <tr>
          <td colspan="3" style="padding: 15px; text-align: center; color: #a0aec0;">No se encontraron registros.</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
```

---

## 4. Buenas Prácticas y Seguridad

1. **Inline CSS:** Los clientes de correo electrónico (Gmail, Outlook, etc.) no leen archivos CSS externos ni selectores globales `<style>` de forma confiable. Siempre escribe tus estilos usando el atributo inline `style="..."`.
2. **Sanitización Automática:** Toda salida HTML generada por el nodo EMail se sanitiza automáticamente utilizando **nh3** en el backend para bloquear código malicioso (`<script>`, inyecciones), manteniendo tu flujo robusto y seguro.
