<template>
    <div class="min-h-screen w-full bg-slate-50 flex justify-center items-start" :class="outerClass">
        <div class="w-full" :class="containerClass">
          <slot />
        </div>
    </div>
</template>

<script setup lang="ts">
type Props = {
  /** 外層額外 class*/
  outerClass?: string;
  /** 內容容器 class*/
  containerClass?: string;
};

withDefaults(defineProps<Props>(), {
  outerClass: "py-10",
  containerClass: "px-6 w-full max-w-xl mx-auto",
});
</script>
