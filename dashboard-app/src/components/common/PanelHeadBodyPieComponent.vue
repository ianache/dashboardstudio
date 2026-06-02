<template>
  <div class="panel-head-body-pie" :class="{ 'is-expanded': isExpanded, 'has-footer': showFooter }">
    <!-- Header -->
    <div class="panel-header" @click="toggleExpand">
      <div class="panel-header-icon" v-if="icon">
        <span class="material-symbols-outlined">{{ icon }}</span>
      </div>
      <div class="panel-header-content">
        <h3 class="panel-title">{{ title }}</h3>
        <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
      </div>
      <div class="panel-header-actions">
        <slot name="header-actions"></slot>
        <span class="panel-toggle-icon">
          {{ isExpanded ? '▲' : '▼' }}
        </span>
      </div>
    </div>

    <!-- Body -->
    <div v-show="isExpanded" class="panel-body">
      <slot name="body">
        <div class="panel-body-default">
          <slot></slot>
        </div>
      </slot>
    </div>

    <!-- Footer -->
    <div v-if="showFooter && isExpanded" class="panel-footer">
      <div class="panel-footer-content">
        <slot name="footer-left"></slot>
      </div>
      <div class="panel-footer-actions">
        <slot name="footer-actions">
          <button 
            v-if="showResetButton" 
            class="panel-btn panel-btn-secondary"
            @click="$emit('reset')"
          >
            {{ resetButtonText }}
          </button>
          <button 
            v-if="showApplyButton" 
            class="panel-btn panel-btn-primary"
            @click="$emit('apply')"
          >
            {{ applyButtonText }}
          </button>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  // Header props
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  
  // Expand/Collapse props
  expanded: {
    type: Boolean,
    default: false
  },
  
  // Footer control props
  showFooter: {
    type: Boolean,
    default: true
  },
  
  // Footer button props
  showResetButton: {
    type: Boolean,
    default: true
  },
  showApplyButton: {
    type: Boolean,
    default: true
  },
  resetButtonText: {
    type: String,
    default: 'Reset'
  },
  applyButtonText: {
    type: String,
    default: 'Apply Changes'
  }
})

const emit = defineEmits(['expand', 'collapse', 'toggle', 'reset', 'apply'])

const isExpanded = ref(props.expanded)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
  emit('toggle', isExpanded.value)
  if (isExpanded.value) {
    emit('expand')
  } else {
    emit('collapse')
  }
}
</script>

<style scoped>
.panel-head-body-pie {
  background: var(--card-bg);
  border: 1px solid var(--outline);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}

.panel-head-body-pie:hover {
  box-shadow: var(--shadow-md);
}

/* Header Styles */
.panel-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  background: var(--surface-container-high);
  border-bottom: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.panel-header:hover {
  background: rgba(173, 198, 255, 0.05);
}

.is-expanded .panel-header {
  border-bottom-color: var(--outline);
}

.panel-header-icon {
  width: 40px;
  height: 40px;
  background: rgba(173, 198, 255, 0.1);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.panel-header-icon .material-symbols-outlined {
  font-size: 22px;
  color: var(--primary);
}

.panel-header-content {
  flex: 1;
  min-width: 0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--on-surface);
  margin: 0 0 4px 0;
  line-height: 1.3;
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.01em;
}

.panel-subtitle {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin: 0;
  line-height: 1.4;
}

.panel-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.panel-toggle-icon {
  font-size: 12px;
  color: var(--on-surface-variant);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

/* Body Styles */
.panel-body {
  padding: 20px;
  background: var(--card-bg);
}

.panel-body-default {
  min-height: 100px;
}

/* Footer Styles */
.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--surface-container-low);
  border-top: 1px solid var(--outline);
  gap: 16px;
}

.panel-footer-content {
  flex: 1;
}

.panel-footer-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* Button Styles */
.panel-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.panel-btn-secondary {
  background: transparent;
  color: var(--on-surface);
  border-color: var(--outline);
}

.panel-btn-secondary:hover {
  background: rgba(173, 198, 255, 0.05);
  border-color: var(--primary);
  color: var(--primary);
}

.panel-btn-primary {
  background: var(--primary-container);
  color: var(--on-primary-container);
}

.panel-btn-primary:hover {
  background: #0066d6;
  box-shadow: 0 0 12px rgba(173, 198, 255, 0.3);
}

/* Material Symbols Font */
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}

/* Responsive */
@media (max-width: 640px) {
  .panel-footer {
    flex-direction: column;
    align-items: stretch;
  }
  
  .panel-footer-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .panel-btn {
    flex: 1;
  }
}
</style>
