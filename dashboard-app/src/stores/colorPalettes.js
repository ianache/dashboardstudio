import { defineStore } from 'pinia'
import { paletteApi } from '@/services/api'

const BUILT_IN_PALETTES = [
  {
    id: 'default',
    label: 'Predeterminada',
    colors: ['#1890ff','#52c41a','#faad14','#f5222d','#722ed1','#13c2c2','#fa8c16','#eb2f96','#2f54eb','#a0d911']
  },
  {
    id: 'ocean',
    label: 'Océano',
    colors: ['#003f5c','#2f6b9a','#1890ff','#36cfc9','#87e8de','#006d75','#08979c','#13c2c2','#5cdbd3','#b5f5ec']
  },
  {
    id: 'sunset',
    label: 'Atardecer',
    colors: ['#7b2d00','#d4380d','#fa541c','#fa8c16','#faad14','#ffc53d','#ffe58f','#eb2f96','#c41d7f','#9e1068']
  },
  {
    id: 'forest',
    label: 'Bosque',
    colors: ['#092b00','#135200','#237804','#389e0d','#52c41a','#73d13d','#95de64','#b7eb8f','#6abe39','#2d8653']
  },
  {
    id: 'pastel',
    label: 'Pastel',
    colors: ['#91caff','#b7eb8f','#ffe58f','#ffadd2','#d3adf7','#87e8de','#ffd591','#ffa39e','#adc6ff','#d9f7be']
  },
  {
    id: 'vivid',
    label: 'Vívida',
    colors: ['#003eb3','#0050b3','#1890ff','#00b5d8','#00c9a7','#52c41a','#fadb14','#fa8c16','#f5222d','#eb2f96']
  },
  {
    id: 'earth',
    label: 'Tierra',
    colors: ['#3b1f0e','#6b3a2a','#9c5634','#c87941','#d4935a','#e0b07b','#a8764b','#7c5c3c','#5c3d2e','#2d2010']
  },
  {
    id: 'mono',
    label: 'Monocromática',
    colors: ['#003a8c','#0050b3','#096dd9','#1890ff','#40a9ff','#69c0ff','#91d5ff','#bae7ff','#0d47a1','#1565c0']
  }
]

export const useColorPaletteStore = defineStore('colorPalettes', {
  state: () => ({
    palettes: [],
    defaultPaletteId: null,
    loading: false,
    error: null
  }),

  getters: {
    allPalettes: (state) => state.palettes,
    defaultPalette: (state) => state.palettes.find(p => p.id === state.defaultPaletteId) ?? null,
    getPaletteById: (state) => (id) => state.palettes.find(p => p.id === id) ?? null
  },

  actions: {
    async loadFromBackend() {
      this.loading = true
      this.error = null
      try {
        const palettes = await paletteApi.getAll()
        // Transform backend format to frontend format
        this.palettes = palettes.map(p => ({
          id: p.id,
          label: p.label,
          colors: p.colors,
          is_default: p.is_default,
          created_by: p.created_by
        }))
        // Set default palette ID
        const defaultPalette = this.palettes.find(p => p.is_default)
        this.defaultPaletteId = defaultPalette?.id ?? null
      } catch (err) {
        this.error = err.message
        console.warn('Failed to load palettes from backend:', err)
        // Fallback to built-in palettes
        this.palettes = BUILT_IN_PALETTES
        this.defaultPaletteId = 'default'
      } finally {
        this.loading = false
      }
    },

    async addPalette(label, colors) {
      try {
        const palette = await paletteApi.create({
          label,
          colors,
          is_default: false
        })
        this.palettes.push({
          id: palette.id,
          label: palette.label,
          colors: palette.colors,
          is_default: palette.is_default
        })
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    },

    async updatePalette(id, label, colors) {
      try {
        const palette = await paletteApi.update(id, {
          label,
          colors
        })
        const idx = this.palettes.findIndex(p => p.id === id)
        if (idx !== -1) {
          this.palettes[idx] = {
            ...this.palettes[idx],
            label: palette.label,
            colors: palette.colors
          }
        }
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    },

    async deletePalette(id) {
      try {
        await paletteApi.delete(id)
        this.palettes = this.palettes.filter(p => p.id !== id)
        if (this.defaultPaletteId === id) this.defaultPaletteId = null
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    },

    async setDefault(id) {
      try {
        await paletteApi.setDefault(id)
        // Update local state
        this.palettes.forEach(p => {
          p.is_default = p.id === id
        })
        this.defaultPaletteId = id
        return { success: true }
      } catch (err) {
        return { success: false, error: err.message }
      }
    },

    resetToBuiltIn() {
      this.palettes = BUILT_IN_PALETTES
      this.defaultPaletteId = 'default'
    }
  }
})

/** Standalone helper — use the store when inside a component */
export function getPaletteColors(paletteId, palettes) {
  const list = palettes ?? BUILT_IN_PALETTES
  return list.find(p => p.id === paletteId)?.colors ?? list[0]?.colors ?? []
}

// Re-export built-in list so existing static imports keep working
export const COLOR_PALETTES = BUILT_IN_PALETTES
