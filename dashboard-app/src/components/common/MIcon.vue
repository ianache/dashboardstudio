<template>
  <span
    class="material-symbols-outlined"
    :class="sizeClass"
    :style="varStyle"
    aria-hidden="true"
  >{{ icon }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, required: true },
  /** Optical size — also controls font-size: 20 | 24 | 40 | 48 */
  size: { type: Number, default: 24 },
  /** Fill: 0 (outlined) or 1 (filled) */
  fill: { type: Number, default: 0 },
  /** Stroke weight: 100 – 700 */
  weight: { type: Number, default: 400 },
  /** Grade/emphasis: -50 | 0 | 200 */
  grade: { type: Number, default: 0 },
})

const varStyle = computed(() => ({
  fontVariationSettings: `'FILL' ${props.fill}, 'wght' ${props.weight}, 'GRAD' ${props.grade}, 'opsz' ${props.size}`,
  fontSize: `${props.size}px`,
}))

const sizeClass = computed(() => `m-icon-opsz-${props.size}`)
</script>
