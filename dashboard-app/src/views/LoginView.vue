<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <rect width="48" height="48" rx="12" fill="#1890ff"/>
          <rect x="8" y="18" width="8" height="20" rx="2" fill="white"/>
          <rect x="20" y="10" width="8" height="28" rx="2" fill="white"/>
          <rect x="32" y="22" width="8" height="16" rx="2" fill="white"/>
        </svg>
        <div>
          <h1>Dashboard<strong>Studio</strong></h1>
          <p>Diseña y visualiza tus datos</p>
        </div>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>

        <div class="form-group">
          <label class="form-label">Correo electrónico</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="correo@ejemplo.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Contraseña</label>
          <div class="input-password">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              placeholder="••••••••"
              required
              autocomplete="current-password"
            />
            <button type="button" class="password-toggle" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <span v-if="loading" class="btn-spinner"></span>
          <span v-else>Iniciar sesión</span>
        </button>
      </form>

      <!-- Demo credentials -->
      <div class="demo-creds">
        <div class="demo-title">Credenciales de demo</div>
        <div class="demo-list">
          <div
            v-for="cred in demoCredentials"
            :key="cred.email"
            class="demo-item"
            @click="fillCredentials(cred)"
          >
            <div class="demo-avatar" :style="{ background: cred.color }">{{ cred.avatar }}</div>
            <div>
              <div class="demo-name">{{ cred.name }}</div>
              <div class="demo-role">{{ cred.role }}</div>
              <code class="demo-email-code">{{ cred.email }} / {{ cred.password }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

const demoCredentials = [
  { name: 'Ana García', role: 'Diseñadora', email: 'admin@demo.com', password: 'admin123', avatar: 'AG', color: '#1890ff' },
  { name: 'Carlos López', role: 'Visualizador', email: 'viewer@demo.com', password: 'viewer123', avatar: 'CL', color: '#52c41a' }
]

function fillCredentials(cred) {
  email.value = cred.email
  password.value = cred.password
}

async function handleLogin() {
  if (!email.value || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #001529 0%, #003a8c 100%);
  padding: 24px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}
.login-logo h1 {
  font-size: 20px;
  font-weight: 400;
  color: var(--text);
  margin: 0;
}
.login-logo h1 strong { font-weight: 700; }
.login-logo p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.login-form { display: flex; flex-direction: column; gap: 16px; }

.input-password { position: relative; }
.input-password .form-input { padding-right: 40px; }
.password-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  padding: 4px;
}
.password-toggle:hover { color: var(--text); }

.login-btn {
  width: 100%;
  justify-content: center;
  padding: 10px;
  font-size: 15px;
  margin-top: 4px;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

/* Demo credentials */
.demo-creds {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}
.demo-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
.demo-list { display: flex; flex-direction: column; gap: 8px; }
.demo-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.demo-item:hover { border-color: var(--primary); background: var(--primary-light); }
.demo-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.demo-name { font-size: 13px; font-weight: 600; color: var(--text); }
.demo-role { font-size: 11px; color: var(--text-secondary); margin: 2px 0; }
.demo-email-code { font-size: 11px; color: var(--primary); font-family: monospace; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
