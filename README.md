
# Iniciar

```
npm run dev   # → http://localhost:3000
```

Credenciales demo:

  - Diseñador: admin@demo.com / admin123
  - Visualizador: viewer@demo.com / viewer123

  Flujo de trabajo:

  1. El diseñador crea dashboards → añade widgets → configura tipo de gráfico + query CubeJS
  2. El diseñador asigna dashboards a usuarios visualizadores
  3. El visualizador ve sus dashboards en el submenú lateral "Dashboards"
  4. Todos los widgets tienen refresh de datos y descarga CSV desde la cabecera

  CubeJS:

  - Sin configurar → usa datos de demostración automáticamente
  - Configura URL + Token en Configuración → Conexión CubeJS
  - El modal de configuración del widget incluye un explorador del esquema Cube para arrastrar medidas/dimensiones