/**
 * API client for backend services
 * Automatically includes Keycloak token for authentication
 */
import keycloak from '@/services/keycloak'

// Use the backend URL from env or default to port 8000 (matching backend .env)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

async function getAuthHeaders() {
  // Check if keycloak is initialized and has a token
  if (!keycloak.authenticated) {
    throw new Error('Not authenticated - Keycloak not initialized')
  }
  
  const token = keycloak.token
  if (!token) {
    throw new Error('Not authenticated - No token available')
  }
  
  // Refresh token if it will expire in less than 30 seconds
  if (keycloak.isTokenExpired(30)) {
    try {
      await keycloak.updateToken(30)
    } catch (err) {
      console.error('Failed to refresh token:', err)
      throw new Error('Session expired - Please login again')
    }
  }
  
  return {
    'Authorization': `Bearer ${keycloak.token}`,
    'Content-Type': 'application/json'
  }
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = await getAuthHeaders()

  console.log(`[API] ${options.method || 'GET'} ${url}`)
  console.log(`[API] Token available: ${!!keycloak.token}`)
  console.log(`[API] Token prefix: ${keycloak.token ? keycloak.token.substring(0, 50) + '...' : 'none'}`)

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options.headers
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    console.error(`[API] Error ${response.status}:`, errorData)
    throw new ApiError(
      errorData?.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      errorData
    )
  }

  // Return null for 204 No Content
  if (response.status === 204) {
    return null
  }

  return response.json()
}

// Cube Config API
export const cubeConfigApi = {
  async getAll() {
    return apiRequest('/api/v1/cube-config/')
  },

  async getActive() {
    return apiRequest('/api/v1/cube-config/active')
  },

  async getById(id) {
    return apiRequest(`/api/v1/cube-config/${id}`)
  },

  async create(config) {
    return apiRequest('/api/v1/cube-config/', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  async update(id, config) {
    return apiRequest(`/api/v1/cube-config/${id}`, {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/cube-config/${id}`, {
      method: 'DELETE'
    })
  },

  async activate(id) {
    return apiRequest(`/api/v1/cube-config/${id}/activate`, {
      method: 'POST'
    })
  }
}

// LLM Config API
export const llmConfigApi = {
  async getAll() {
    return apiRequest('/api/v1/llm-config/')
  },

  async getProviders() {
    return apiRequest('/api/v1/llm-config/providers')
  },

  async save(provider, apiKey) {
    return apiRequest('/api/v1/llm-config/', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey })
    })
  },

  async delete(provider) {
    return apiRequest(`/api/v1/llm-config/${provider}`, {
      method: 'DELETE'
    })
  },

  async deleteAll() {
    return apiRequest('/api/v1/llm-config/', {
      method: 'DELETE'
    })
  }
}

// Palette Config API
export const paletteApi = {
  async getAll() {
    return apiRequest('/api/v1/palettes/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/palettes/${id}`)
  },

  async create(palette) {
    return apiRequest('/api/v1/palettes/', {
      method: 'POST',
      body: JSON.stringify(palette)
    })
  },

  async update(id, palette) {
    return apiRequest(`/api/v1/palettes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(palette)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/palettes/${id}`, {
      method: 'DELETE'
    })
  },

  async setDefault(id) {
    return apiRequest(`/api/v1/palettes/${id}/default`, {
      method: 'POST'
    })
  }
}

// Dashboard API
export const dashboardApi = {
  async getAll() {
    return apiRequest('/api/v1/dashboards/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/dashboards/${id}`)
  },

  async create(dashboard) {
    return apiRequest('/api/v1/dashboards/', {
      method: 'POST',
      body: JSON.stringify(dashboard)
    })
  },

  async update(id, dashboard) {
    return apiRequest(`/api/v1/dashboards/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dashboard)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/dashboards/${id}`, {
      method: 'DELETE'
    })
  },

  async assign(id, userIds) {
    return apiRequest(`/api/v1/dashboards/${id}/assign`, {
      method: 'POST',
      body: JSON.stringify({ user_ids: userIds })
    })
  },

  async addFilter(dashboardId, filterData) {
    return apiRequest(`/api/v1/dashboards/${dashboardId}/filters`, {
      method: 'POST',
      body: JSON.stringify(filterData)
    })
  },

  async removeFilter(dashboardId, filterId) {
    return apiRequest(`/api/v1/dashboards/${dashboardId}/filters/${filterId}`, {
      method: 'DELETE'
    })
  },

  // Widget methods
  async createWidget(dashboardId, widget) {
    return apiRequest(`/api/v1/dashboards/${dashboardId}/widgets/`, {
      method: 'POST',
      body: JSON.stringify(widget)
    })
  },

  async updateWidget(dashboardId, widgetId, widget) {
    return apiRequest(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`, {
      method: 'PUT',
      body: JSON.stringify(widget)
    })
  },

  async deleteWidget(dashboardId, widgetId) {
    return apiRequest(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`, {
      method: 'DELETE'
    })
  }
}

// Dimensional Model API
export const dimensionalModelApi = {
  async getAll() {
    return apiRequest('/api/v1/dimensional-models/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/dimensional-models/${id}`)
  },

  async create(model) {
    return apiRequest('/api/v1/dimensional-models/', {
      method: 'POST',
      body: JSON.stringify(model)
    })
  },

  async update(id, model) {
    return apiRequest(`/api/v1/dimensional-models/${id}`, {
      method: 'PUT',
      body: JSON.stringify(model)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/dimensional-models/${id}`, {
      method: 'DELETE'
    })
  },

  async setGlobal(id) {
    return apiRequest(`/api/v1/dimensional-models/${id}/global`, {
      method: 'POST'
    })
  }
}

// Currencies API
export const currenciesApi = {
  async getAll() {
    return apiRequest('/api/v1/currencies/')
  }
}

// Data Sources API
export const dataSourcesApi = {
  async getAll() {
    return apiRequest('/api/v1/data-sources/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/data-sources/${id}`)
  },

  async getByName(name) {
    return apiRequest(`/api/v1/data-sources/by-name/${encodeURIComponent(name)}`)
  },

  async search(query) {
    return apiRequest(`/api/v1/data-sources/search?q=${encodeURIComponent(query)}`)
  },

  async create(dataSource) {
    return apiRequest('/api/v1/data-sources/', {
      method: 'POST',
      body: JSON.stringify(dataSource)
    })
  },

  async update(id, dataSource) {
    return apiRequest(`/api/v1/data-sources/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dataSource)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/data-sources/${id}`, {
      method: 'DELETE'
    })
  },

  async testConnection(id) {
    return apiRequest(`/api/v1/data-sources/${id}/test`, {
      method: 'POST'
    })
  }
}

// Knowledge Spaces API
export const knowledgeSpacesApi = {
  async getAll() {
    return apiRequest('/api/v1/knowledge-spaces/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/knowledge-spaces/${id}`)
  },

  async getByName(name) {
    return apiRequest(`/api/v1/knowledge-spaces/by-name/${encodeURIComponent(name)}`)
  },

  async search(query) {
    return apiRequest(`/api/v1/knowledge-spaces/search?q=${encodeURIComponent(query)}`)
  },

  async create(space) {
    return apiRequest('/api/v1/knowledge-spaces/', {
      method: 'POST',
      body: JSON.stringify(space)
    })
  },

  async update(id, space) {
    return apiRequest(`/api/v1/knowledge-spaces/${id}`, {
      method: 'PUT',
      body: JSON.stringify(space)
    })
  },

  async delete(id) {
    return apiRequest(`/api/v1/knowledge-spaces/${id}`, {
      method: 'DELETE'
    })
  }
}

// Diagram Types API
export const diagramTypesApi = {
  async getAll() { return apiRequest('/api/v1/diagram-types/') },
  async getById(id) { return apiRequest(`/api/v1/diagram-types/${id}`) },
  async create(dt) { return apiRequest('/api/v1/diagram-types/', { method: 'POST', body: JSON.stringify(dt) }) },
  async update(id, dt) { return apiRequest(`/api/v1/diagram-types/${id}`, { method: 'PUT', body: JSON.stringify(dt) }) },
  async delete(id) { return apiRequest(`/api/v1/diagram-types/${id}`, { method: 'DELETE' }) },
}

// Editor Tools API
export const editorToolsApi = {
  async getAll(params = {}) {
    const q = new URLSearchParams(params).toString()
    return apiRequest(`/api/v1/editor-tools/${q ? '?' + q : ''}`)
  },
  async getById(id) { return apiRequest(`/api/v1/editor-tools/${id}`) },
  async getForDiagram(diagramType) { return apiRequest(`/api/v1/editor-tools/?diagram_type=${encodeURIComponent(diagramType)}`) },
  async create(tool) { return apiRequest('/api/v1/editor-tools/', { method: 'POST', body: JSON.stringify(tool) }) },
  async update(id, tool) { return apiRequest(`/api/v1/editor-tools/${id}`, { method: 'PUT', body: JSON.stringify(tool) }) },
  async delete(id) { return apiRequest(`/api/v1/editor-tools/${id}`, { method: 'DELETE' }) },
}

// Integration Flows API
export const integrationFlowsApi = {
  async getAll(params = {}) {
    const q = new URLSearchParams(params).toString()
    return apiRequest(`/api/v1/integration-flows/${q ? '?' + q : ''}`)
  },
  async getById(id) { return apiRequest(`/api/v1/integration-flows/${id}`) },
  async create(flow) { return apiRequest('/api/v1/integration-flows/', { method: 'POST', body: JSON.stringify(flow) }) },
  async update(id, flow) { return apiRequest(`/api/v1/integration-flows/${id}`, { method: 'PUT', body: JSON.stringify(flow) }) },
  async saveDiagram(id, diagramData) { return apiRequest(`/api/v1/integration-flows/${id}/diagram`, { method: 'PUT', body: JSON.stringify(diagramData) }) },
  async delete(id) { return apiRequest(`/api/v1/integration-flows/${id}`, { method: 'DELETE' }) },
  
  async getLatestExecution(flowId) {
    const results = await apiRequest(`/api/v1/integration-flows/${flowId}/executions?limit=1`)
    return results && results.length > 0 ? results[0] : null
  },
  async getExecutionLogs(execId) {
    return apiRequest(`/api/v1/integration-flows/executions/${execId}/logs`)
  },

  async getHistory(flowId) { return apiRequest(`/api/v1/execution-history/${flowId}`) },
  async getExecutionDetail(executionId) { return apiRequest(`/api/v1/execution-history/detail/${executionId}`) }
}

// Users API
export const usersApi = {
  async getAll() {
    return apiRequest('/api/v1/users/')
  },

  async getById(id) {
    return apiRequest(`/api/v1/users/${id}`)
  },

  async getMe() {
    return apiRequest('/api/v1/users/me')
  },

  /**
   * Upsert user records from Keycloak data before dashboard assignment.
   * @param {Array<{id, email, full_name, first_name, last_name, username}>} users
   */
  async provisionBatch(users) {
    return apiRequest('/api/v1/users/provision-batch', {
      method: 'POST',
      body: JSON.stringify(users)
    })
  }
}

export default {
  cubeConfig: cubeConfigApi,
  llmConfig: llmConfigApi,
  palette: paletteApi,
  dashboard: dashboardApi,
  dimensionalModel: dimensionalModelApi,
  currencies: currenciesApi,
  dataSources: dataSourcesApi,
  knowledgeSpaces: knowledgeSpacesApi,
  diagramTypes: diagramTypesApi,
  editorTools: editorToolsApi,
  integrationFlows: integrationFlowsApi,
  users: usersApi,
}
