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
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s ease;
}

.panel-head-body-pie:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Header Styles */
.panel-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.panel-header:hover {
  background: #f0f0f0;
}

.is-expanded .panel-header {
  border-bottom-color: #e2e8f0;
}

.panel-header-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.panel-header-icon .material-symbols-outlined {
  font-size: 22px;
  color: #2563eb;
}

.panel-header-content {
  flex: 1;
  min-width: 0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 4px 0;
  line-height: 1.3;
}

.panel-subtitle {
  font-size: 13px;
  color: #64748b;
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
  color: #94a3b8;
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
  background: white;
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
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
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
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.panel-btn-secondary {
  background: white;
  color: #475569;
  border-color: #cbd5e1;
}

.panel-btn-secondary:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.panel-btn-primary {
  background: #2563eb;
  color: white;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.panel-btn-primary:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3);
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
