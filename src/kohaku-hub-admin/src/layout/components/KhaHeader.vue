<template>
  <div class="header-title">
    <h1
      class="text-xl font-semibold text-gray-900 dark:text-gray-100 none-select"
    >
      {{ siteName }} Administration
    </h1>
  </div>

  <div class="header-actions">
    <el-button @click="openGlobalSearch" class="search-button">
      <div class="i-carbon-search text-lg" />
      <span class="ml-2 hidden sm:inline">Search</span>
      <el-tag size="small" effect="plain" class="ml-2 hidden md:inline">
        Ctrl+K
      </el-tag>
    </el-button>
    <el-button circle @click="themeStore.toggle()" class="mr-2">
      <div v-if="themeStore.isDark" class="i-carbon-moon text-lg" />
      <div v-else class="i-carbon-asleep text-lg" />
    </el-button>
    <el-button type="danger" @click="handleLogout" :icon="SwitchButton">
      Logout
    </el-button>
  </div>
</template>
<script setup>
import { inject } from "vue";
import { useThemeStore } from "@/stores/theme";
import { useAdminStore } from "@/stores/admin";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { SwitchButton } from "@element-plus/icons-vue";

const router = useRouter();

const openGlobalSearch = inject("openGlobalSearch");

const themeStore = useThemeStore();
const adminStore = useAdminStore();

const siteName = ref("KohakuHub");

function handleLogout() {
  adminStore.logout();
  ElMessage.success("Logged out successfully");
  router.push("/login");
}
</script>
<style scoped>
.none-select {
  -moz-user-select: -moz-none;
  -khtml-user-select: none;
  -webkit-user-select: none;
  -o-user-select: none;
  user-select: none;
}
</style>
