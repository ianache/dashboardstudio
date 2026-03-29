<template>
  <div class="auth-redirect">
    <div class="auth-redirect-card">
      <div class="auth-logo">
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
      <div class="auth-spinner"></div>
      <p class="auth-message">Redirigiendo al servidor de autenticación...</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import keycloak from '@/services/keycloak'

onMounted(() => {
  // If somehow this page is reached and Keycloak is not authenticated, redirect to Keycloak login
  if (!keycloak.authenticated) {
    keycloak.login()
  }
})
</script>

<style scoped>
.auth-redirect {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #001529 0%, #003a8c 100%);
}

.auth-redirect-card {
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.auth-logo {
  display: flex;
  align-items: center;
  gap: 16px;
}
.auth-logo h1 {
  font-size: 20px;
  font-weight: 400;
  color: var(--text);
  margin: 0;
}
.auth-logo h1 strong { font-weight: 700; }
.auth-logo p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.auth-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e6f4ff;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.auth-message {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
