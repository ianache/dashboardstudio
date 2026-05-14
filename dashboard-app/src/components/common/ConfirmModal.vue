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
  background: rgba(15, 23, 42, 0.55);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
  animation: cm-fade-in 0.15s ease;
}
@keyframes cm-fade-in { from { opacity: 0 } to { opacity: 1 } }

.cm-dialog {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.28);
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
  width: 40px; height: 40px; border-radius: 10px;
  background: #fef9c3; color: #854d0e;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.cm-question-ico .cm-msi { font-size: 22px; }

.cm-text { flex: 1; min-width: 0; }
.cm-question {
  font-size: 15px; font-weight: 700; color: #0f172a;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  margin: 0 0 4px; line-height: 1.4;
}
.cm-detail { font-size: 13px; color: #64748b; margin: 0; line-height: 1.5; }

.cm-footer {
  display: flex; align-items: center; justify-content: flex-end; gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid #f1f5f9;
  background: #f8fafc;
}

.cm-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  border: 1px solid transparent; transition: all 0.15s;
  font-family: inherit;
}

.cm-btn--cancel {
  background: #fff; color: #475569;
  border-color: #e2e8f0;
}
.cm-btn--cancel:hover { background: #f1f5f9; border-color: #cbd5e1; }

.cm-btn--primary {
  background: #2563eb; color: #fff;
  border-color: #2563eb;
}
.cm-btn--primary:hover { background: #1d4ed8; border-color: #1d4ed8; }

.cm-btn--danger {
  background: #dc2626; color: #fff;
  border-color: #dc2626;
}
.cm-btn--danger:hover { background: #b91c1c; border-color: #b91c1c; }
</style>
