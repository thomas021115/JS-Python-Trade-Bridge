<script setup lang="ts">
import { computed } from "vue";

type Variant = "center" | "wide" | "full";

type Props = {
  outerClass?: string;
  containerClass?: string;
  variant?: Variant;
};

const props = withDefaults(defineProps<Props>(), {
  outerClass: "py-10",
  variant: "center",
  containerClass: "",
});

const variantClassMap: Record<Variant, string> = {
  center: "px-6 w-full max-w-xl mx-auto",
  wide: "px-6 w-full max-w-6xl mx-auto",
  full: "px-6 w-full",
};

const computedContainerClass = computed(() => {
  // 允許 containerClass 覆蓋/補充
  return [variantClassMap[props.variant], props.containerClass].join(" ").trim();
});
</script>

<template>
  <div class="min-h-screen w-full bg-slate-50 flex justify-center items-start" :class="outerClass">
    <div :class="computedContainerClass">
      <slot />
    </div>
  </div>
</template>

