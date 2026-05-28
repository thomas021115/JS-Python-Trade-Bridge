<script setup lang="ts">
type Tone = 'default' | 'aurum';

withDefaults(defineProps<{ tone?: Tone }>(), {
  tone: 'default',
});
</script>

<template>
  <div
    class="w-full transition-all duration-300"
    :class="
      tone === 'aurum'
        ? 'rounded-2xl border border-amber-300/25 bg-slate-950/80 p-5 shadow-2xl shadow-black/40 backdrop-blur sm:p-8'
        : 'max-w-xl rounded-2xl bg-white p-8 shadow-xl ring-1 ring-slate-900/5'
    "
  >
    <slot />
  </div>
</template>
