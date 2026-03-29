# Store: colorPalettes

**Archivo:** `src/stores/colorPalettes.js`

Gestiona las paletas de colores disponibles en la aplicación — tanto las predefinidas como las creadas por los diseñadores. Incluye soporte para definir una paleta predeterminada del sistema.

## Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `palettes` | `Palette[]` | Lista de todas las paletas disponibles |
| `defaultPaletteId` | `String \| null` | ID de la paleta predeterminada del sistema (`null` = sin predeterminada) |

### Estructura `Palette`

```javascript
{
  id: string,       // ID único ('default', 'ocean', 'pal_abc123', ...)
  label: string,    // Nombre visible
  colors: string[]  // Array de colores hex (mínimo 6, recomendado 10)
}
```

## Getters

| Getter | Retorna | Descripción |
|---|---|---|
| `allPalettes` | `Palette[]` | Todas las paletas |
| `defaultPalette` | `Palette \| null` | Paleta con `id === defaultPaletteId` |
| `getPaletteById(id)` | `Palette \| null` | Busca una paleta por ID |

## Acciones

| Acción | Parámetros | Descripción |
|---|---|---|
| `addPalette(label, colors)` | `string, string[]` | Crea nueva paleta con ID generado |
| `updatePalette(id, label, colors)` | `string, string, string[]` | Actualiza nombre y colores |
| `deletePalette(id)` | `string` | Elimina la paleta (no se puede eliminar la última) |
| `setDefault(id)` | `string` | Establece/quita predeterminada (toggle) |
| `resetToBuiltIn()` | — | Restaura las 8 paletas predefinidas y limpia el default |

## Paletas predefinidas

| ID | Nombre |
|---|---|
| `default` | Predeterminada |
| `ocean` | Océano |
| `sunset` | Atardecer |
| `forest` | Bosque |
| `pastel` | Pastel |
| `vivid` | Vívida |
| `earth` | Tierra |
| `mono` | Monocromática |

## Persistencia

Se guarda en `localStorage['colorPalettes']`:

```json
{
  "palettes": [...],
  "defaultPaletteId": "ocean"
}
```

Si no existe la clave, se inicializa con las 8 paletas predefinidas y sin predeterminada.

## Lógica de herencia de paleta en widgets

La resolución de color en `EChartWrapper` sigue este orden de prioridad:

```
widget.colorPalette === 'none'  →  sin paleta (usa colores propios de medidas)
widget.colorPalette === <id>    →  paleta específica del widget
dashboardPalette prop           →  paleta del dashboard
paletteStore.defaultPaletteId  →  paleta predeterminada del sistema
(fallback)                      →  array COLORS hardcoded
```

### Valores especiales de `widget.colorPalette`

| Valor | Significado |
|---|---|
| `null` / `undefined` | Hereda del contexto (dashboard → sistema → fallback) |
| `'none'` | Deshabilita la herencia; usa colores de medidas |
| `'ocean'`, `'forest'`… | Paleta específica, anula herencia |
