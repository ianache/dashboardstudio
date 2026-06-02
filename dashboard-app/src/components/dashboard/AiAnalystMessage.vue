<template>
  <div class="ai-msg" :class="message.role === 'user' ? 'ai-msg--user' : (message.role === 'divider' ? 'ai-msg--divider' : 'ai-msg--assistant')">

    <!-- DIVIDER — model switch marker -->
    <template v-if="message.role === 'divider'">
      <div class="ai-switch-divider">
        <div class="ai-switch-line"></div>
        <span class="ai-switch-label">{{ message.label }}</span>
        <div class="ai-switch-line"></div>
      </div>
    </template>

    <!-- USER message -->
    <template v-else-if="message.role === 'user'">
      <div class="ai-bubble-user">{{ message.content }}</div>
    </template>

    <!-- ASSISTANT message -->
    <template v-else>
      <!-- Avatar + "AI ANALYST" label + model badge -->
      <div class="ai-agent-id">
        <div class="ai-agent-avatar">
          <span class="material-symbols-outlined" style="font-variation-settings:'FILL' 1">psychology</span>
        </div>
        <span class="ai-agent-label">AI ANALYST</span>
        <span v-if="message.model" class="ai-model-badge">
          {{ modelLabel(message.model) }}
        </span>
      </div>

      <!-- Error state -->
      <div v-if="message.error" class="ai-card ai-card--error">
        <span class="material-symbols-outlined ai-error-icon">error</span>
        <p>{{ message.content }}</p>
      </div>

      <!-- Normal card -->
      <div v-else class="ai-card">
        <!-- Streaming dots (no content yet) -->
        <div v-if="message.streaming && !hasAnyContent" class="ai-dots">
          <span class="ai-dot"></span>
          <span class="ai-dot"></span>
          <span class="ai-dot"></span>
        </div>

        <!-- ── Analyzing panel (tool calls + intermediate thinking) ── -->
        <AiCollapsiblePanel
          v-if="hasAnalyzingContent"
          label="Analyzing"
          icon="manage_search"
          variant="analyzing"
          :expanded="false"
          :streaming="message.streaming && !message.content"
          :badge="analyzingBadge"
          class="acp-incard"
        >
          <div class="ai-analyzing-body">
            <!-- Tool calls -->
            <div
              v-for="(tc, i) in message.toolCalls"
              :key="'tc' + i"
              class="ai-tool-row ai-tool-row--call"
            >
              <span class="ai-tool-arrow material-symbols-outlined">arrow_forward</span>
              <span class="ai-tool-name">{{ formatToolName(tc.name) }}</span>
              <span v-if="tc.args && Object.keys(tc.args).length" class="ai-tool-args">
                {{ formatArgs(tc.args) }}
              </span>
            </div>
            <!-- Tool results -->
            <div
              v-for="(tr, i) in message.toolResults"
              :key="'tr' + i"
              class="ai-tool-row ai-tool-row--result"
            >
              <span class="ai-tool-arrow material-symbols-outlined">arrow_back</span>
              <span class="ai-tool-name">{{ formatToolName(tr.name) }}</span>
              <span v-if="tr.rows != null" class="ai-tool-rows">{{ tr.rows }} rows</span>
            </div>
            <!-- Thinking text -->
            <div v-if="message.thinking" class="ai-thinking-text">
              {{ message.thinking }}
            </div>
          </div>
        </AiCollapsiblePanel>

        <!-- ── Results panel ── -->
        <AiCollapsiblePanel
          v-if="message.content || message.streaming"
          label="Results"
          icon="check_circle"
          variant="results"
          :expanded="true"
          :streaming="message.streaming && !!message.content"
          class="acp-incard"
          :class="{ 'acp-incard--top': hasAnalyzingContent }"
        >
          <div class="ai-result-body">
            <div v-if="message.content" class="ai-content" v-html="renderedContent"></div>
            <div v-else-if="message.streaming" class="ai-dots ai-dots--inline">
              <span class="ai-dot"></span>
              <span class="ai-dot"></span>
              <span class="ai-dot"></span>
            </div>
            <span v-if="message.streaming && message.content" class="ai-cursor"></span>
          </div>
        </AiCollapsiblePanel>

        <!-- Skill CTA buttons -->
        <div v-if="message.skills && message.skills.length" class="ai-skill-ctas">
          <button
            v-for="skill in message.skills"
            :key="skill.name"
            class="ai-skill-btn"
            :disabled="store.loading"
            @click="store.executeSkill(skill.name, skill.params || {})"
          >
            <span class="material-symbols-outlined ai-skill-icon">play_arrow</span>
            {{ skill.label || skill.name }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useAiAnalystStore } from '@/stores/aiAnalyst'
import AiCollapsiblePanel from '@/components/dashboard/AiCollapsiblePanel.vue'

const store = useAiAnalystStore()

const props = defineProps({
  message: { type: Object, required: true }
})

const MODEL_LABELS = {
  'gemini-2.5-flash-lite':     'Gemini Flash',
  'deepseek/deepseek-v4-flash': 'DeepSeek V4 Flash',
  'deepseek/deepseek-v4-pro':   'DeepSeek V4 Pro',
  'groq/llama-3.3-70b-versatile': 'Llama 3.3 70B',
}

function modelLabel(modelId) {
  return MODEL_LABELS[modelId] || modelId
}

function formatToolName(name) {
  if (!name) return '?'
  return name.replace(/_/g, ' ')
}

function formatArgs(args) {
  if (!args) return ''
  // Show only the most informative fields, truncated
  const entries = Object.entries(args)
    .map(([k, v]) => {
      const val = typeof v === 'object' ? JSON.stringify(v) : String(v)
      return `${k}: ${val.length > 40 ? val.slice(0, 40) + '…' : val}`
    })
    .slice(0, 3)
  return entries.join(' · ')
}

const hasAnalyzingContent = computed(() =>
  (props.message.toolCalls && props.message.toolCalls.length > 0) ||
  (props.message.toolResults && props.message.toolResults.length > 0) ||
  !!props.message.thinking
)

const hasAnyContent = computed(() =>
  !!props.message.content ||
  !!props.message.thinking ||
  (props.message.toolCalls && props.message.toolCalls.length > 0)
)

const analyzingBadge = computed(() => {
  const calls = (props.message.toolCalls || []).length
  const results = (props.message.toolResults || []).length
  const total = calls + results
  return total > 0 ? total : null
})

marked.setOptions({ breaks: true, gfm: true })

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
.ai-msg {
  --c-surface:      #111319;
  --c-container:    #1d2026;
  --c-high:         #272a30;
  --c-low:          #191b22;
  --c-lowest:       #0c0e14;
  --c-outline-v:    #424753;
  --c-primary:      #adc6ff;
  --c-primary-c:    #0058bc;
  --c-on-primary:   #002e69;
  --c-on-primary-c: #c3d4ff;
  --c-secondary:    #b7c8e1;
  --c-secondary-c:  #3a4a5f;
  --c-tertiary:     #ffb595;
  --c-on-surface:   #e1e2eb;
  --c-on-sv:        #c2c6d5;

  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: 'Inter', system-ui, sans-serif;
}

.ai-msg--user      { align-items: flex-end; }
.ai-msg--assistant { align-items: flex-start; }

/* ── User bubble ── */
.ai-bubble-user {
  max-width: 85%;
  background: rgba(58, 74, 95, 0.4);
  color: var(--c-on-surface);
  padding: 12px 14px;
  border-radius: 12px 0 12px 12px;
  border: 1px solid rgba(66, 71, 83, 0.2);
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* ── Agent identity row ── */
.ai-agent-id {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-agent-avatar {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: rgba(0, 88, 188, 0.2);
  border: 1px solid rgba(173, 198, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-primary);
  flex-shrink: 0;
}

.ai-agent-avatar .material-symbols-outlined { font-size: 14px; }

.ai-agent-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--c-primary);
}

/* ── Glass card ── */
.ai-card {
  width: 100%;
  background: rgba(30, 36, 51, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0;
  transition: border-color 0.2s;
}

.ai-card:hover { border-color: rgba(173, 198, 255, 0.15); }

.ai-card--error {
  width: 100%;
  background: rgba(147, 0, 10, 0.15);
  border: 1px solid rgba(255, 180, 171, 0.2);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #ffb4ab;
  font-size: 14px;
}

.ai-card--error .ai-error-icon { font-size: 18px; flex-shrink: 0; }
.ai-card--error p { margin: 0; }

/* ── AiCollapsiblePanel inside the card ── */
.acp-incard {
  border-radius: 0;
  border: none;
  border-bottom: 1px solid rgba(66, 71, 83, 0.25);
  background: transparent;
}

.acp-incard:last-child { border-bottom: none; }

.acp-incard--top {
  border-top: 1px solid rgba(66, 71, 83, 0.25);
}

/* ── Streaming dots ── */
.ai-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 16px;
}

.ai-dots--inline {
  padding: 12px 14px;
}

.ai-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-on-sv);
  opacity: 0.6;
  animation: ai-bounce 1.2s ease-in-out infinite;
}

.ai-dot:nth-child(2) { animation-delay: 0.2s; }
.ai-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes ai-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
  40%            { transform: scale(1.2); opacity: 1; }
}

/* ── Analyzing body ── */
.ai-analyzing-body {
  padding: 10px 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(25, 27, 34, 0.5);
}

.ai-tool-row {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  font-size: 12px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  line-height: 1.4;
}

.ai-tool-row--call   { color: var(--c-secondary); }
.ai-tool-row--result { color: var(--c-on-sv); opacity: 0.75; }

.ai-tool-arrow {
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 1px;
}

.ai-tool-name {
  font-weight: 600;
  text-transform: capitalize;
  flex-shrink: 0;
}

.ai-tool-args {
  opacity: 0.6;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-all;
}

.ai-tool-rows {
  background: rgba(173, 198, 255, 0.08);
  color: var(--c-primary);
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid rgba(173, 198, 255, 0.15);
  flex-shrink: 0;
}

.ai-thinking-text {
  font-size: 12px;
  color: var(--c-on-sv);
  opacity: 0.65;
  font-style: italic;
  line-height: 1.55;
  white-space: pre-wrap;
  border-top: 1px solid rgba(66, 71, 83, 0.2);
  padding-top: 6px;
  margin-top: 2px;
}

/* ── Results body ── */
.ai-result-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ── Markdown content ── */
.ai-content {
  font-size: 14px;
  line-height: 1.65;
  color: var(--c-on-surface);
}

.ai-content :deep(p)              { margin: 0 0 8px 0; }
.ai-content :deep(p:last-child)   { margin-bottom: 0; }
.ai-content :deep(ul),
.ai-content :deep(ol)             { margin: 6px 0 6px 16px; padding: 0; }
.ai-content :deep(li)             { margin-bottom: 2px; }
.ai-content :deep(code) {
  background: rgba(58, 74, 95, 0.3);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 12px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  color: var(--c-secondary);
}
.ai-content :deep(pre) {
  background: var(--c-lowest);
  color: var(--c-on-sv);
  border-radius: 8px;
  padding: 10px 14px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid var(--c-outline-v);
}
.ai-content :deep(pre code)    { background: transparent; padding: 0; color: inherit; }
.ai-content :deep(blockquote)  {
  border-left: 3px solid var(--c-outline-v);
  margin: 6px 0;
  padding: 2px 10px;
  color: var(--c-on-sv);
}
.ai-content :deep(h1),
.ai-content :deep(h2),
.ai-content :deep(h3)          { margin: 10px 0 4px; font-weight: 700; color: var(--c-on-surface); }
.ai-content :deep(h1)          { font-size: 16px; }
.ai-content :deep(h2)          { font-size: 15px; }
.ai-content :deep(h3)          { font-size: 14px; }
.ai-content :deep(table)       { border-collapse: collapse; width: 100%; font-size: 12px; margin: 8px 0; }
.ai-content :deep(th),
.ai-content :deep(td)          { border: 1px solid var(--c-outline-v); padding: 4px 8px; text-align: left; }
.ai-content :deep(th)          { background: var(--c-high); font-weight: 600; }
.ai-content :deep(a)           { color: var(--c-primary); text-decoration: underline; }

/* ── Streaming cursor ── */
.ai-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: var(--c-on-sv);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: ai-blink 0.9s step-end infinite;
}

@keyframes ai-blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* ── Skill CTA buttons ── */
.ai-skill-ctas {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 14px;
  border-top: 1px solid rgba(66, 71, 83, 0.3);
}

.ai-skill-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid rgba(173, 198, 255, 0.3);
  background: transparent;
  color: var(--c-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  font-family: 'Inter', system-ui, sans-serif;
}

.ai-skill-btn:hover:not(:disabled) {
  background: var(--c-primary);
  color: var(--c-on-primary);
}

.ai-skill-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.ai-skill-icon         { font-size: 14px; }

/* ── Model switch divider ── */
.ai-msg--divider { align-items: stretch; }

.ai-switch-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 2px 0;
}

.ai-switch-line {
  flex: 1;
  height: 1px;
  background: rgba(66, 71, 83, 0.3);
}

.ai-switch-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--c-on-sv);
  opacity: 0.4;
  white-space: nowrap;
}

/* ── Model badge ── */
.ai-model-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--c-tertiary);
  opacity: 0.7;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid rgba(255, 181, 149, 0.2);
  background: rgba(255, 181, 149, 0.06);
}
</style>
