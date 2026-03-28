import { defineStore } from 'pinia'

export const BASE_TYPES = [
  { value: 'SMALLINT',         hasSize: false, hasPrecision: false },
  { value: 'INTEGER',          hasSize: false, hasPrecision: false },
  { value: 'BIGINT',           hasSize: false, hasPrecision: false },
  { value: 'SERIAL',           hasSize: false, hasPrecision: false },
  { value: 'BIGSERIAL',        hasSize: false, hasPrecision: false },
  { value: 'NUMERIC',          hasSize: true,  hasPrecision: true  },
  { value: 'DECIMAL',          hasSize: true,  hasPrecision: true  },
  { value: 'REAL',             hasSize: false, hasPrecision: false },
  { value: 'DOUBLE PRECISION', hasSize: false, hasPrecision: false },
  { value: 'MONEY',            hasSize: false, hasPrecision: false },
  { value: 'CHAR',             hasSize: true,  hasPrecision: false },
  { value: 'VARCHAR',          hasSize: true,  hasPrecision: false },
  { value: 'TEXT',             hasSize: false, hasPrecision: false },
  { value: 'BOOLEAN',          hasSize: false, hasPrecision: false },
  { value: 'DATE',             hasSize: false, hasPrecision: false },
  { value: 'TIME',             hasSize: false, hasPrecision: false },
  { value: 'TIMESTAMP',        hasSize: false, hasPrecision: false },
  { value: 'TIMESTAMPTZ',      hasSize: false, hasPrecision: false },
  { value: 'UUID',             hasSize: false, hasPrecision: false },
  { value: 'JSONB',            hasSize: false, hasPrecision: false },
  { value: 'JSON',             hasSize: false, hasPrecision: false },
  { value: 'BYTEA',            hasSize: false, hasPrecision: false },
]

const DEFAULT_TYPES = [
  { id: 'dt-serial',  name: 'Serial',       baseType: 'SERIAL',    size: null, precision: null, description: 'Entero autoincremental (clave primaria)' },
  { id: 'dt-int',     name: 'Entero',        baseType: 'INTEGER',   size: null, precision: null, description: 'Número entero de 32 bits' },
  { id: 'dt-bigint',  name: 'Entero grande', baseType: 'BIGINT',    size: null, precision: null, description: 'Número entero de 64 bits' },
  { id: 'dt-numeric', name: 'Decimal',       baseType: 'NUMERIC',   size: 18,   precision: 4,    description: 'Número decimal de alta precisión' },
  { id: 'dt-money',   name: 'Moneda',        baseType: 'NUMERIC',   size: 18,   precision: 2,    description: 'Valores monetarios' },
  { id: 'dt-pct',     name: 'Porcentaje',    baseType: 'NUMERIC',   size: 5,    precision: 2,    description: 'Valores porcentuales (0-100)' },
  { id: 'dt-varchar', name: 'Texto',         baseType: 'VARCHAR',   size: 255,  precision: null, description: 'Cadena de texto variable' },
  { id: 'dt-text',    name: 'Texto largo',   baseType: 'TEXT',      size: null, precision: null, description: 'Texto sin límite de longitud' },
  { id: 'dt-bool',    name: 'Booleano',      baseType: 'BOOLEAN',   size: null, precision: null, description: 'Verdadero / Falso' },
  { id: 'dt-date',    name: 'Fecha',         baseType: 'DATE',      size: null, precision: null, description: 'Fecha sin hora (YYYY-MM-DD)' },
  { id: 'dt-ts',      name: 'Timestamp',     baseType: 'TIMESTAMP', size: null, precision: null, description: 'Fecha y hora sin zona horaria' },
  { id: 'dt-tstz',    name: 'Timestamp TZ',  baseType: 'TIMESTAMPTZ', size: null, precision: null, description: 'Fecha y hora con zona horaria' },
  { id: 'dt-uuid',    name: 'UUID',          baseType: 'UUID',      size: null, precision: null, description: 'Identificador único universal' },
  { id: 'dt-jsonb',   name: 'JSONB',         baseType: 'JSONB',     size: null, precision: null, description: 'Documento JSON binario indexable' },
]

function generateId() {
  return 'dt-' + Math.random().toString(36).substr(2, 9)
}

function loadTypes() {
  try {
    const saved = localStorage.getItem('dataTypes')
    if (saved) return JSON.parse(saved)
  } catch {}
  return DEFAULT_TYPES.map(t => ({ ...t }))
}

export function sqlTypeString(dt) {
  if (!dt) return ''
  const meta = BASE_TYPES.find(b => b.value === dt.baseType)
  if (!meta) return dt.baseType
  if (meta.hasSize && dt.size != null) {
    if (meta.hasPrecision && dt.precision != null) {
      return `${dt.baseType}(${dt.size},${dt.precision})`
    }
    return `${dt.baseType}(${dt.size})`
  }
  return dt.baseType
}

export const useDataTypeStore = defineStore('dataTypes', {
  state: () => ({
    types: loadTypes()
  }),

  getters: {
    allTypes: (state) => state.types,
    getById: (state) => (id) => state.types.find(t => t.id === id) || null,
    sqlOf: (state) => (id) => {
      const dt = state.types.find(t => t.id === id)
      return dt ? sqlTypeString(dt) : id   // fallback: return raw value
    }
  },

  actions: {
    persist() {
      localStorage.setItem('dataTypes', JSON.stringify(this.types))
    },

    addType({ name, baseType, size, precision, description }) {
      const dt = {
        id: generateId(),
        name: name || 'Nuevo tipo',
        baseType: baseType || 'VARCHAR',
        size: size ?? null,
        precision: precision ?? null,
        description: description || ''
      }
      this.types.push(dt)
      this.persist()
      return dt
    },

    updateType(id, patch) {
      const dt = this.types.find(t => t.id === id)
      if (!dt) return
      Object.assign(dt, patch)
      // Clear size/precision if base type no longer supports them
      const meta = BASE_TYPES.find(b => b.value === dt.baseType)
      if (meta && !meta.hasSize)      { dt.size = null; dt.precision = null }
      if (meta && !meta.hasPrecision) { dt.precision = null }
      this.persist()
    },

    deleteType(id) {
      const idx = this.types.findIndex(t => t.id === id)
      if (idx !== -1) { this.types.splice(idx, 1); this.persist() }
    },

    resetToDefaults() {
      this.types = DEFAULT_TYPES.map(t => ({ ...t }))
      this.persist()
    }
  }
})
