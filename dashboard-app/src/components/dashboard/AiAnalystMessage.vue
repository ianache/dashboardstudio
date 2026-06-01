<template>
  <div class="ai-message" :class="message.role === 'user' ? 'ai-message--user' : 'ai-message--assistant'">
    <!-- User message -->
    <div v-if="message.role === 'user'" class="ai-message-bubble ai-message-bubble--user">
      <p class="ai-message-text">{{ message.content }}</p>
    </div>

    <!-- Assistant message -->
    <template v-else>
      <!-- Error state -->
      <div v-if="message.error" class="ai-message-bubble ai-message-bubble--error">
        <span class="material-symbols-outlined ai-message-error-icon">error</span>
        <p class="ai-message-text">{{ message.content }}</p>
      </div>

      <div v-else class="ai-message-bubble ai-message-bubble--assistant">
        <!-- Thought section (collapsible) -->
        <details v-if="message.thought" class="ai-section ai-section--thought">
          <summary class="ai-section-summary">
            <span class="material-symbols-outlined ai-section-icon">psychology</span>
            <span class="ai-section-label">Razonamiento</span>
            <span class="material-symbols-outlined ai-section-chevron">expand_more</span>
          </summary>
          <div class="ai-section-body ai-thought-body">{{ message.thought }}</div>
        </details>

        <!-- Actions Taken section (collapsible) -->
        <details v-if="message.actions && message.actions.length > 0" class="ai-section ai-section--actions">
          <summary class="ai-section-summary ai-section-summary--actions">
            <span class="material-symbols-outlined ai-section-icon">bolt</span>
            <span class="ai-section-label">Acciones realizadas</span>
            <span class="ai-section-badge">{{ message.actions.length }}</span>
            <span class="material-symbols-outlined ai-section-chevron">expand_more</span>
          </summary>
          <div class="ai-section-body ai-actions-body">
            <div v-for="(action, i) in message.actions" :key="i" class="ai-action-item">
              <span class="material-symbols-outlined ai-action-icon">check_circle</span>
              <span class="ai-action-text">{{ typeof action === 'string' ? action : (action.name || action.tool || JSON.stringify(action)) }}</span>
            </div>
          </div>
        </details>

        <!-- Streaming indicator -->
        <div v-if="message.streaming && !message.content" class="ai-streaming-indicator">
          <span class="ai-dot"></span>
          <span class="ai-dot"></span>
          <span class="ai-dot"></span>
        </div>

        <!-- Main content (markdown rendered) -->
        <div
          v-if="message.content"
          class="ai-message-content"
          v-html="renderedContent"
        ></div>

        <!-- Skill CTA buttons -->
        <div v-if="message.skills && message.skills.length > 0" class="ai-skill-ctas">
          <button
            v-for="skill in message.skills"
            :key="skill.name"
            class="ai-skill-btn"
            :disabled="store.loading"
            @click="store.executeSkill(skill.name, skill.params || {})"
          >
            <span class="material-symbols-outlined ai-skill-btn-icon">play_arrow</span>
            {{ skill.label || skill.name }}
          </button>
        </div>

        <!-- Streaming cursor -->
        <span v-if="message.streaming && message.content" class="ai-cursor"></span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useAiAnalystStore } from '@/stores/aiAnalyst'

const store = useAiAnalystStore()

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

// Configure marked for safe rendering
marked.setOptions({
  breaks: true,
  gfm: true
})

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  const raw = marked.parse(props.message.content)
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre',
                   'h1', 'h2', 'h3', 'h4', 'blockquote', 'a', 'table', 'thead',
                   'tbody', 'tr', 'th', 'td', 'span'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class']
  })
})
</script>

<style scoped>
.ai-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-message--user {
  align-items: flex-end;
}

.ai-message--assistant {
  align-items: flex-start;
}

/* Bubbles */
.ai-message-bubble {
  max-width: 90%;
  border-radius: 16px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
}

.ai-message-bubble--user {
  background: var(--primary, #1890ff);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-message-bubble--assistant {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #0f172a;
  border-bottom-left-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-message-bubble--error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 12px;
  max-width: 90%;
  font-size: 14px;
}

.ai-message-error-icon { font-size: 18px; flex-shrink: 0; }

.ai-message-text { margin: 0; }

/* Collapsible sections */
.ai-section {
  border-radius: 8px;
  overflow: hidden;
}

.ai-section--thought {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
}

.ai-section-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  list-style: none;
  font-size: 12px;
  font-weight: 600;
  color: #0369a1;
}

.ai-section-summary::-webkit-details-marker { display: none; }

.ai-section-icon { font-size: 16px; }

.ai-section-label { flex: 1; }

.ai-section-chevron {
  font-size: 18px;
  transition: transform 0.2s;
}

details[open] .ai-section-chevron {
  transform: rotate(180deg);
}

.ai-section-body {
  padding: 8px 10px;
  border-top: 1px solid #bae6fd;
}

.ai-thought-body {
  font-size: 12px;
  color: #475569;
  white-space: pre-wrap;
  line-height: 1.5;
}

/* Main content markdown */
.ai-message-content {
  font-size: 14px;
  line-height: 1.65;
  color: #1e293b;
}

.ai-message-content :deep(p) { margin: 0 0 8px 0; }
.ai-message-content :deep(p:last-child) { margin-bottom: 0; }
.ai-message-content :deep(ul),
.ai-message-content :deep(ol) { margin: 6px 0 6px 16px; padding: 0; }
.ai-message-content :deep(li) { margin-bottom: 2px; }
.ai-message-content :deep(code) {
  background: #e2e8f0;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.ai-message-content :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  overflow-x: auto;
  margin: 8px 0;
}
.ai-message-content :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: 12px;
  color: inherit;
}
.ai-message-content :deep(blockquote) {
  border-left: 3px solid #cbd5e1;
  margin: 6px 0;
  padding: 2px 10px;
  color: #64748b;
}
.ai-message-content :deep(h1),
.ai-message-content :deep(h2),
.ai-message-content :deep(h3) {
  margin: 10px 0 4px;
  font-weight: 700;
  color: #0f172a;
}
.ai-message-content :deep(h1) { font-size: 16px; }
.ai-message-content :deep(h2) { font-size: 15px; }
.ai-message-content :deep(h3) { font-size: 14px; }
.ai-message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
  margin: 8px 0;
}
.ai-message-content :deep(th),
.ai-message-content :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 4px 8px;
  text-align: left;
}
.ai-message-content :deep(th) { background: #f1f5f9; font-weight: 600; }
.ai-message-content :deep(a) { color: #1890ff; text-decoration: underline; }

/* Streaming */
.ai-streaming-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}

.ai-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: ai-bounce 1.2s ease-in-out infinite;
}

.ai-dot:nth-child(2) { animation-delay: 0.2s; }
.ai-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes ai-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1.2); opacity: 1; }
}

.ai-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: #94a3b8;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: ai-blink 0.9s step-end infinite;
}

@keyframes ai-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Actions section */
.ai-section--actions {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.ai-section-summary--actions {
  color: #15803d;
}

.ai-section-badge {
  font-size: 10px;
  font-weight: 700;
  background: #bbf7d0;
  color: #15803d;
  border-radius: 8px;
  padding: 0 5px;
  min-width: 16px;
  text-align: center;
}

.ai-actions-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border-top: 1px solid #bbf7d0;
}

.ai-action-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #166534;
  line-height: 1.4;
}

.ai-action-icon {
  font-size: 14px;
  color: #22c55e;
  flex-shrink: 0;
  margin-top: 1px;
}

.ai-action-text { flex: 1; word-break: break-word; }

/* Skill CTA buttons */
.ai-skill-ctas {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.ai-skill-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 16px;
  border: 1px solid #6366f1;
  background: transparent;
  color: #6366f1;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.ai-skill-btn:hover:not(:disabled) {
  background: #6366f1;
  color: #fff;
}

.ai-skill-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-skill-btn-icon { font-size: 14px; }
</style>
