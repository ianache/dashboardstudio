<template>
  <Teleport to="body">
    <div class="cm-overlay" @click.self="$emit('cancel')">
      <div class="cm-dialog" role="dialog" aria-modal="true">

        <!-- Icon + Question -->
        <div class="cm-body">
          <div class="cm-question-ico">
            <span class="cm-msi">{{ warningIcon }}</span>
          </div>
          <div class="cm-text">
            <p class="cm-question">{{ question }}</p>
            <p v-if="detail" class="cm-detail">{{ detail }}</p>
          </div>
        </div>

        <!-- Actions -->
        <div class="cm-footer">
          <button class="cm-btn cm-btn--cancel" @click="$emit('cancel')">
            <span class="cm-msi">{{ cancelIcon }}</span>
            {{ cancelLabel }}
          </button>
          <button class="cm-btn" :class="`cm-btn--${acceptVariant}`" @click="$emit('accept')">
            <span class="cm-msi">{{ acceptIcon }}</span>
            {{ acceptLabel }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  question:      { type: String,  required: true },
  detail:        { type: String,  default: '' },
  warningIcon:   { type: String,  default: 'help_outline' },
  cancelLabel:   { type: String,  default: 'Cancelar' },
  cancelIcon:    { type: String,  default: 'close' },
  acceptLabel:   { type: String,  default: 'Aceptar' },
  acceptIcon:    { type: String,  default: 'check' },
  acceptVariant: { type: String,  default: 'primary' },   // 'primary' | 'danger'
})
defineEmits(['cancel', 'accept'])
</script>

<style scoped>
.cm-msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 20px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
  white-space: nowrap; direction: ltr; -webkit-font-smoothing: antialiased; flex-shrink: 0;
}

.cm-overlay {
  position: fixed; inset: 0; z-index: 2000;
  background: color-mix(in srgb, var(--on-surface) 40%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
  animation: cm-fade-in 0.15s ease;
}
@keyframes cm-fade-in { from { opacity: 0 } to { opacity: 1 } }

.cm-dialog {
  background: color-mix(in srgb, var(--surface) 80%, transparent);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: var(--radius-xl);
  border: 1px solid var(--outline-variant);
  box-shadow: var(--shadow-lg);
  width: 100%; max-width: 420px;
  overflow: hidden;
  animation: cm-slide-in 0.18s ease;
}
@keyframes cm-slide-in { from { transform: translateY(-12px); opacity: 0 } to { transform: none; opacity: 1 } }

.cm-body {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 24px 24px 20px;
}

.cm-question-ico {
  width: 40px; height: 40px; border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--warning) 12%, transparent);
  color: var(--warning);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.cm-question-ico .cm-msi { font-size: 22px; }

.cm-text { flex: 1; min-width: 0; }
.cm-question {
  font-size: 15px; font-weight: 700; color: var(--on-surface);
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.01em;
  margin: 0 0 4px; line-height: 1.4;
}
.cm-detail { font-size: 13px; color: var(--on-surface-variant); margin: 0; line-height: 1.5; }

.cm-footer {
  display: flex; align-items: center; justify-content: flex-end; gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--outline-variant);
}

.cm-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: var(--radius-md);
  font-size: 13px; font-weight: 600; cursor: pointer;
  border: 1px solid transparent; transition: all 0.15s;
  font-family: inherit;
}

.cm-btn--cancel {
  background: transparent; color: var(--on-surface);
  border-color: var(--outline);
}
.cm-btn--cancel:hover {
  background: color-mix(in srgb, var(--primary) 8%, transparent);
  border-color: var(--primary);
  color: var(--primary);
}

.cm-btn--primary {
  background: var(--primary-container); color: var(--on-primary-container);
  border-color: var(--primary-container);
}
.cm-btn--primary:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--on-primary);
}

.cm-btn--danger {
  background: var(--error-container); color: var(--on-error-container);
  border-color: var(--error-container);
}
.cm-btn--danger:hover {
  background: var(--error);
  border-color: var(--error);
  color: var(--on-error);
}
</style>
