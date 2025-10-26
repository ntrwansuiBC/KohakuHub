<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAdminStore } from "@/stores/admin";
import { useThemeStore } from "@/stores/theme";

const router = useRouter();
const adminStore = useAdminStore();
const themeStore = useThemeStore();

onMounted(() => {
  // Initialize theme
  themeStore.init();

  // Redirect to login if not authenticated
  if (!adminStore.isAuthenticated && router.currentRoute.value.path !== "/") {
    router.push("/");
  }
});
</script>

<template>
  <router-view />
</template>

<style>
/* Global styles are in style.css */
</style>
