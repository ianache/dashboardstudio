<template>
  <div class="code-editor-container" :style="{ height: height }">
    <monaco-editor
      v-model:value="internalValue"
      :language="language"
      :theme="theme"
      :options="mergedOptions"
      @change="handleChange"
      @mount="handleMount"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { VueMonacoEditor as MonacoEditor } from '@guolao/vue-monaco-editor'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language:   { type: String, default: 'javascript' },
  theme:      { type: String, default: 'vs-dark' },
  height:     { type: String, default: '300px' },
  options:    { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:modelValue', 'change'])

const internalValue = ref(props.modelValue)
const editorRef = ref(null)

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

function handleMount(editor) {
  editorRef.value = editor
}
</script>

<style scoped>
.code-editor-container {
  border: 1px solid #d1d5db;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}
</style>
