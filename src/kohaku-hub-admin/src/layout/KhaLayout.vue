<template>
  <el-container class="kha-layout">
    <!-- Sidebar -->
    <el-aside width="250px" class="sidebar">
      <KhaAside :menu-items="menuItems" />
    </el-aside>

    <!-- Main Content -->
    <el-container>
      <!-- Header -->
      <el-header class="header">
        <KhaHeader />
      </el-header>

      <!-- Content -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- Global Search Modal -->
    <GlobalSearch ref="globalSearchRef" />
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from "vue";
import { useRoute } from "vue-router";
import KhaHeader from "./components/KhaHeader.vue";
import GlobalSearch from "@/components/GlobalSearch.vue";
import KhaAside from "./components/KhaAside.vue";

const route = useRoute();

console.log(route);

const globalSearchRef = ref(null);

const menuItems = [
  {
    path: "/container/dashboard",
    label: "Dashboard",
    icon: "i-carbon-dashboard",
  },
  { path: "/container/users", label: "Users", icon: "i-carbon-user-multiple" },
  {
    path: "/container/invitations",
    label: "Invitations",
    icon: "i-carbon-email",
  },
  {
    path: "/container/repositories",
    label: "Repositories",
    icon: "i-carbon-data-base",
  },
  { path: "/container/commits", label: "Commits", icon: "i-carbon-version" },
  {
    path: "/container/storage",
    label: "Storage",
    icon: "i-carbon-data-volume",
  },
  {
    path: "/container/fallback-sources",
    label: "Fallback Sources",
    icon: "i-carbon-connect",
  },
  {
    path: "/container/quota-overview",
    label: "Quota Overview",
    icon: "i-carbon-meter",
  },
  {
    path: "/container/database",
    label: "Database",
    icon: "i-carbon-data-table",
  },
];

function openGlobalSearch() {
  if (globalSearchRef.value) {
    globalSearchRef.value.openDialog();
  }
}

// Keyboard shortcut handler
function handleGlobalKeyDown(event) {
  // Ctrl+K or Cmd+K
  if ((event.ctrlKey || event.metaKey) && event.key === "k") {
    event.preventDefault();
    openGlobalSearch();
  }
}

onMounted(() => {
  window.addEventListener("keydown", handleGlobalKeyDown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleGlobalKeyDown);
});

provide("openGlobalSearch", openGlobalSearch);
</script>

<style scoped>
.kha-layout {
  height: 100vh;
  background-color: var(--bg-base);
}

.sidebar {
  background-color: var(--bg-elevated);
  border-right: 1px solid var(--border-default);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.sidebar-header {
  display: flex;
  align-items: center;
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-light);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.sidebar-header h2 {
  color: white !important;
}

.sidebar-menu {
  border-right: none;
  background-color: var(--bg-elevated) !important;
}

.header {
  background-color: var(--bg-elevated);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.header-title {
  flex: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-button {
  border-color: var(--border-default);
  background-color: var(--bg-hover);
  transition: all 0.2s ease;
}

.search-button:hover {
  border-color: var(--color-info);
  background-color: var(--bg-active);
}

.main-content {
  background-color: var(--bg-base);
  min-height: calc(100vh - 60px);
}
</style>
