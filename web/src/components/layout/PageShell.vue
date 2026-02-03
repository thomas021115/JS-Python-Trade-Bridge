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
