<template>
  <component
    :is="resolvedIcon"
    :size="size"
    :stroke-width="strokeWidth"
    :color="iconColor"
    class="m-icon-adapter"
    aria-hidden="true"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from 'vue'
import { HelpCircle } from 'lucide-vue-next'
import * as LucideIcons from 'lucide-vue-next'
import { iconMap } from './IconMap.js'

// Pre-calculate a normalized map of all Lucide icons for fast case-insensitive lookup
const normalizedLucideMap = {}
for (const [key, value] of Object.entries(LucideIcons)) {
  const normalizedKey = key.toLowerCase().replace(/[^a-z0-9]/g, '')
  normalizedLucideMap[normalizedKey] = value
}

// Avoid double-binding attributes on the root component if it's not needed,
// but here we want to pass class/style to the lucide component.
defineOptions({
  inheritAttrs: false
})

const props = defineProps({
  icon: { type: String, required: true },
  /** Optical size — also controls dimensions */
  size: { type: [Number, String], default: 24 },
  /** Fill: 0 (outlined) or 1 (filled). Legacy prop. */
  fill: { type: Number, default: 0 },
  /** Stroke weight: 100 – 700. Mapped to stroke-width. */
  weight: { type: Number, default: 400 },
  /** Grade/emphasis: -50 | 0 | 200. Legacy prop. */
  grade: { type: Number, default: 0 },
  /** Explicit color override */
  color: { type: String, default: null }
})

const resolvedIcon = computed(() => {
  if (!props.icon) return HelpCircle
  
  // 1. Direct check in the predefined iconMap (legacy Material to Lucide names)
  if (iconMap[props.icon]) {
    return iconMap[props.icon]
  }
  
  // 2. Case-insensitive lookup in all Lucide icons
  const normalizedSearch = props.icon.toLowerCase().replace(/[^a-z0-9]/g, '')
  if (normalizedLucideMap[normalizedSearch]) {
    return normalizedLucideMap[normalizedSearch]
  }
  
  // 3. Fallback to HelpCircle
  return HelpCircle
})

const strokeWidth = computed(() => {
  // Map legacy material weights to Lucide stroke-width.
  // Success criteria mentions 1.5-2 range.
  return props.weight > 400 ? 2 : 1.5
})

const iconColor = computed(() => {
  // Use explicit color prop, otherwise fall back to theme variable
  return props.color || 'var(--on-surface-variant)'
})
</script>

<style scoped>
.m-icon-adapter {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  /* Ensure the icon doesn't overflow its container */
  max-width: 100%;
  max-height: 100%;
}
</style>
