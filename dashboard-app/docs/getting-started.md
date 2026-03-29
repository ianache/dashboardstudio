# Guía de inicio

## Requisitos previos

- Node.js 18+
- npm 9+
- (Opcional) CubeJS corriendo en `http://localhost:4000`

## Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd dashboard-app

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`.

## Conexion con Keycloak

Roles en Keycloak (realm roles)

  ┌──────────┬────────────────────────────────────────┐
  │   Rol    │                 Acceso                 │
  ├──────────┼────────────────────────────────────────┤
  │ admin    │ Todo (designer + settings)             │
  ├──────────┼────────────────────────────────────────┤
  │ designer │ Crear/editar dashboards y modelos      │
  ├──────────┼────────────────────────────────────────┤
  │ viewer   │ Solo ver dashboards asignados/públicos │
  └──────────┴────────────────────────────────────────┘

  Setup requerido en Keycloak

  1. Crear realm dashboard
  2. Crear client dashboard-app (tipo: public, redirect URI: http://localhost:3000/*)
  3. Crear realm roles: admin, designer, viewer
  4. Asignar roles a usuarios desde Keycloak Admin Console

## Credenciales de demo

| Rol | Email | Contraseña |
|---|---|---|
| Diseñador | admin@demo.com | admin123 |
| Visualizador | viewer@demo.com | viewer123 |
| Visualizador | maria@demo.com | maria123 |

## Configuración de CubeJS (opcional)

Si tienes una instancia de CubeJS:

1. Ve a **Configuración** en el menú lateral
2. Ingresa la URL de la API (ej: `http://localhost:4000/cubejs-api/v1`)
3. Ingresa el token JWT
4. Haz clic en **Probar conexión**

Sin CubeJS configurado, todos los widgets usan **datos simulados** automáticamente.

También puedes configurar CubeJS mediante variables de entorno:

```env
VITE_CUBEJS_API_URL=http://localhost:4000/cubejs-api/v1
VITE_CUBEJS_TOKEN=<jwt-token>
```

## Build de producción

```bash
npm run build    # Genera dist/
npm run preview  # Sirve el build localmente
```

## Primera vez como Diseñador

1. **Inicia sesión** con admin@demo.com
2. Ve a **DISEÑO → Mis Dashboards**
3. Haz clic en **+ Nuevo Dashboard**
4. Ingresa nombre y descripción → **Crear**
5. En el editor, haz clic en **+ Añadir widget**
6. Configura el tipo de gráfico y (si tienes CubeJS) la consulta
7. Arrastra y redimensiona los widgets en el canvas
8. Cambia a **modo Preview** para ver el resultado final

## Primera vez con Modelos Dimensionales

1. Ve a **MODELOS → Ver todos**
2. Haz clic en **Nuevo Modelo**
3. En el editor, usa **+ Hecho** y **+ Dimensión** para añadir tablas
4. Define los campos de cada tabla en el panel de propiedades (derecha)
5. Arrastra el icono ⠿ del campo llave de una dimensión hasta una tabla de hechos para crear la relación
6. Exporta el modelo con los botones de la barra:
   - **DDL/SQL**: genera sentencias `CREATE TABLE`
   - **CubeJS**: genera archivos `.js` de cubos (en ZIP)
   - **YAML**: exporta el modelo para respaldo o importación

## Estructura de datos persistida

Toda la información se guarda en `localStorage` del navegador. Para limpiar el estado:

```javascript
// En la consola del navegador
localStorage.clear()
location.reload()
```
