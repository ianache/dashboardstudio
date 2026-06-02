<template>
  <div class="acp" :class="[`acp--${variant}`, { 'acp--open': isOpen, 'acp--streaming': streaming }]">
    <!-- Header / toggle -->
    <button class="acp-header" @click="toggle" :aria-expanded="isOpen">
      <!-- Left: icon + label + streaming pulse -->
      <span class="acp-icon material-symbols-outlined" aria-hidden="true">{{ icon }}</span>
      <span class="acp-label">{{ label }}</span>
      <span v-if="streaming" class="acp-pulse" aria-hidden="true"></span>
      <span v-if="badge != null" class="acp-badge">{{ badge }}</span>
      <!-- Right: chevron -->
      <span class="acp-chevron material-symbols-outlined" aria-hidden="true">
        expand_more
      </span>
    </button>

    <!-- Body (collapsible) -->
    <div v-show="isOpen" class="acp-body">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  label:     { type: String,  required: true },
  icon:      { type: String,  default: 'info' },
  variant:   { type: String,  default: 'default' }, // 'analyzing' | 'results' | 'default'
  expanded:  { type: Boolean, default: false },      // initial open state
  badge:     { type: [Number, String], default: null },
  streaming: { type: Boolean, default: false },
})

const isOpen = ref(props.expanded)

// Re-sync if parent changes `expanded` prop (e.g. after streaming completes)
watch(() => props.expanded, (v) => { isOpen.value = v })

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<style scoped>
/* ── Design tokens (same palette as AiAnalystPanel) ── */
.acp {
  --c-surface:      #111319;
  --c-container:    #1d2026;
  --c-high:         #272a30;
  --c-low:          #191b22;
  --c-lowest:       #0c0e14;
  --c-outline-v:    #424753;
  --c-primary:      #adc6ff;
  --c-primary-c:    #0058bc;
  --c-secondary:    #b7c8e1;
  --c-tertiary:     #ffb595;
  --c-on-surface:   #e1e2eb;
  --c-on-sv:        #c2c6d5;

  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(66, 71, 83, 0.35);
  background: rgba(17, 19, 25, 0.6);
  font-family: 'Inter', system-ui, sans-serif;
  transition: border-color 0.2s;
}

.acp:hover { border-color: rgba(66, 71, 83, 0.6); }

/* ── Variant tints ── */
.acp--analyzing { border-color: rgba(183, 200, 225, 0.18); }
.acp--analyzing .acp-header { background: rgba(58, 74, 95, 0.25); }
.acp--analyzing .acp-icon,
.acp--analyzing .acp-label  { color: var(--c-secondary); }

.acp--results { border-color: rgba(173, 198, 255, 0.18); }
.acp--results .acp-header { background: rgba(0, 88, 188, 0.12); }
.acp--results .acp-icon,
.acp--results .acp-label  { color: var(--c-primary); }

/* ── Header ── */
.acp-header {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 100%;
  padding: 9px 12px;
  border: none;
  background: rgba(39, 42, 48, 0.5);
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
  font-family: inherit;
}

.acp-header:hover { background: rgba(66, 71, 83, 0.35); }

.acp-icon {
  font-size: 15px;
  color: var(--c-on-sv);
  opacity: 0.7;
  flex-shrink: 0;
}

.acp-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--c-on-sv);
  flex: 1;
  line-height: 1;
}

.acp-badge {
  font-size: 10px;
  font-weight: 700;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  color: var(--c-on-sv);
  opacity: 0.55;
  background: rgba(66, 71, 83, 0.4);
  border-radius: 999px;
  padding: 1px 7px;
  flex-shrink: 0;
}

.acp-chevron {
  font-size: 18px;
  color: var(--c-on-sv);
  opacity: 0.5;
  transition: transform 0.22s ease;
  flex-shrink: 0;
}

.acp--open .acp-chevron { transform: rotate(180deg); }

/* ── Streaming pulse dot ── */
.acp-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-tertiary);
  opacity: 0.85;
  flex-shrink: 0;
  animation: acp-pulse-kf 1.2s ease-in-out infinite;
}

@keyframes acp-pulse-kf {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50%       { transform: scale(1.2); opacity: 1; }
}

/* ── Body ── */
.acp-body {
  border-top: 1px solid rgba(66, 71, 83, 0.3);
}
</style>
