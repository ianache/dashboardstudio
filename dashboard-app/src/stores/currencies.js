import { defineStore } from 'pinia'
import { currenciesApi } from '@/services/api'

export const useCurrencyStore = defineStore('currencies', {
  state: () => ({
    currencies: [],
    loading: false
  }),

  getters: {
    activeCurrencies: (state) => state.currencies.filter(c => c.is_active),
    getById: (state) => (id) => state.currencies.find(c => c.id === id) || null
  },

  actions: {
    async loadFromBackend() {
      if (this.currencies.length > 0) return
      this.loading = true
      try {
        this.currencies = await currenciesApi.getAll()
      } catch (e) {
        console.error('[currencies] Failed to load:', e)
      } finally {
        this.loading = false
      }
    }
  }
})
