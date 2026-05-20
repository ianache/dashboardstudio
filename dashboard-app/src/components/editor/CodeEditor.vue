<template>
  <div 
    class="code-editor-container" 
    :style="containerStyle"
    @mousedown="handleMouseDown"
  >
    <div class="code-editor-toolbar">
      <span class="code-editor-lang">{{ language }}</span>
      <button class="code-editor-ai-btn" @click="showAi = true" title="IA Coding Assistant">
        <span class="msi">auto_awesome</span>
        AI Assist
      </button>
    </div>
    <div class="monaco-wrapper">
      <monaco-editor
        v-model:value="internalValue"
        :language="language"
        :theme="theme"
        :options="mergedOptions"
        @change="handleChange"
        @mount="handleMount"
      />
    </div>

    <CodeAiAssist
      v-if="showAi"
      :initial-language="language"
      :context="internalValue"
      @close="showAi = false"
      @apply="handleApplyAiCode"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { VueMonacoEditor as MonacoEditor } from '@guolao/vue-monaco-editor'
import CodeAiAssist from './CodeAiAssist.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language:   { type: String, default: 'javascript' },
  theme:      { type: String, default: 'vs-dark' },
  height:     { type: String, default: 'auto' },
  options:    { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:modelValue', 'change'])

const internalValue = ref(props.modelValue)
const editorRef = ref(null)
const showAi = ref(false)
const autoHeight = ref(150)
const isManualResize = ref(false)

const containerStyle = computed(() => {
  if (isManualResize.value) {
    return { minHeight: '150px' } // Let CSS resize take over
  }
  return { height: autoHeight.value + 'px' }
})

const defaultOptions = {
  automaticLayout: true,
  minimap: { enabled: false },
  fontSize: 13,
  scrollBeyondLastLine: false,
  lineNumbers: 'on',
  roundedSelection: false,
  readOnly: false,
  cursorStyle: 'line',
  tabSize: 2,
  wordWrap: 'on',
  wrappingStrategy: 'advanced',
  scrollbar: {
    vertical: 'hidden',
    horizontal: 'hidden'
  }
}

const mergedOptions = computed(() => ({
  ...defaultOptions,
  ...props.options
}))

watch(() => props.modelValue, (newVal) => {
  if (newVal !== internalValue.value) {
    internalValue.value = newVal
  }
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}

function updateHeight() {
  if (!editorRef.value || isManualResize.value) return
  const contentHeight = editorRef.value.getContentHeight()
  autoHeight.value = Math.max(150, contentHeight + 40)
}

function handleMount(editor) {
  editorRef.value = editor

  editor.onDidContentSizeChange(() => {
    updateHeight()
  })

  // Initial height
  nextTick(() => {
    updateHeight()
  })
}

function handleMouseDown(e) {
  // Check if click is near the bottom-right corner (resize handle area)
  const rect = e.currentTarget.getBoundingClientRect()
  const isNearBottom = e.clientY > rect.bottom - 20
  const isNearRight = e.clientX > rect.right - 20
  
  if (isNearBottom && isNearRight) {
    isManualResize.value = true
  }
}

function handleApplyAiCode(code) {
  internalValue.value = code
  handleChange(code)
}
</script>

<style scoped>
.code-editor-container {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
  width: 100%;
  display: flex;
  flex-direction: column;
  resize: vertical;
  min-height: 150px;
}

.code-editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.monaco-wrapper {
  flex: 1;
  min-height: 0;
}

.code-editor-lang {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  letter-spacing: 0.05em;
}

.code-editor-ai-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #10b98144;
  background: #ecfdf5;
  color: #059669;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.code-editor-ai-btn:hover {
  background: #d1fae5;
  border-color: #10b98166;
}

.msi {
  font-family: 'Material Symbols Outlined';
  font-weight: normal; font-style: normal; font-size: 16px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
}
</style>