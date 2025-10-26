<template>
  <div class="kha-aside">
    <div class="kha-aside-header">
      <div
        class="i-carbon-security text-2xl text-blue-600 dark:text-blue-400"
      />
      <h2
        class="text-xl font-bold ml-2 text-gray-900 dark:text-gray-100 none-select"
      >
        Admin Portal
      </h2>
    </div>
    <el-menu
      :default-active="route.path"
      router
      class="kha-aside-menu"
      :background-color="themeStore.isDark ? '#1f1f1f' : '#ffffff'"
      :text-color="themeStore.isDark ? '#e0e0e0' : '#303133'"
      :active-text-color="'#409EFF'"
    >
      <el-menu-item
        v-for="item in props.menuItems"
        :key="item.path"
        :index="item.path"
      >
        <div :class="item.icon" class="mr-2" />
        <span class="none-select">{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { defineProps } from "vue";
import { useRoute } from "vue-router";
import { useThemeStore } from "@/stores/theme";

const route = useRoute();

const themeStore = useThemeStore();

const props = defineProps({
  menuItems: {
    type: Array,
    required: true,
    default: () => [],
  },
});
</script>

<style scoped>
.sidebar {
  background-color: var(--bg-elevated);
  border-right: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.kha-aside-header {
  display: flex;
  align-items: center;
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.kha-aside-header h2 {
  color: white !important;
}

.kha-aside-menu {
  border-right: none;
  background-color: var(--bg-elevated) !important;
}

.none-select {
  -moz-user-select: -moz-none;
  -khtml-user-select: none;
  -webkit-user-select: none;
  -o-user-select: none;
  user-select: none;
}
</style>
