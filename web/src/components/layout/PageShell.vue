<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'center' | 'wide' | 'full';
type Theme = 'default' | 'aurum';

type Props = {
  outerClass?: string;
  containerClass?: string;
  variant?: Variant;
  theme?: Theme;
};

const props = withDefaults(defineProps<Props>(), {
  outerClass: 'py-10',
  variant: 'center',
  theme: 'default',
  containerClass: '',
});

const variantClassMap: Record<Variant, string> = {
  center: 'px-4 w-full max-w-2xl mx-auto sm:px-6',
  wide: 'px-4 w-full max-w-6xl mx-auto sm:px-6',
  full: 'px-4 w-full sm:px-6',
};

const themeClassMap: Record<Theme, string> = {
  default:
    'bg-[radial-gradient(circle_at_top_left,rgba(212,175,55,0.10),transparent_34%),linear-gradient(135deg,#020617_0%,#030712_48%,#050816_100%)] text-slate-100',
  aurum:
    'bg-[radial-gradient(circle_at_top_left,rgba(212,175,55,0.16),transparent_34%),linear-gradient(135deg,#020617_0%,#07111f_48%,#0b1020_100%)] text-slate-100',
};

const computedContainerClass = computed(() => {
  return [variantClassMap[props.variant], props.containerClass].join(' ').trim();
});
</script>

<template>
  <div
    class="min-h-screen w-full justify-center overflow-x-hidden"
    :class="[themeClassMap[theme], outerClass]"
  >
    <div :class="computedContainerClass">
      <slot />
    </div>
  </div>
</template>
