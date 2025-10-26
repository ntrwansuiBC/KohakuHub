<template>
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">
        {{ title }}
      </h1>
      <span class="subtitle">
        {{ subtitle }}
      </span>
    </div>

    <slot name="extra"></slot>
  </div>
</template>

<script setup>

const props = defineProps({
  title: {
    type: String,
    default: "Title",
  },
  subtitle: {
    type: String,
    default: "",
  },
});
</script>

<style scoped>
.subtitle {
  color: var(--el-text-color-secondary);
  margin: 0;
}
</style>
