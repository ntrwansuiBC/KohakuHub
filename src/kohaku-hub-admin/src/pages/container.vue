<template>
  <KhaLayout />
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import KhaLayout from "@/layout/KhaLayout.vue";
import StatsCard from "@/components/StatsCard.vue";
import ChartCard from "@/components/ChartCard.vue";
import { useAdminStore } from "@/stores/admin";
import {
  getDetailedStats,
  getTopRepositories,
  getTimeseriesStats,
  getQuotaOverview,
} from "@/utils/api";
import { formatBytes } from "@/utils/api";
import { ElMessage } from "element-plus";

const router = useRouter();
const adminStore = useAdminStore();
const stats = ref(null);
const topRepos = ref([]);
const loading = ref(false);
const timeseriesData = ref(null);
const chartDays = ref(30);
const quotaOverview = ref(null);

const hasData = computed(() => stats.value !== null);

async function loadStats() {
  if (!adminStore.token) {
    router.push("/login");
    return;
  }

  loading.value = true;
  try {
    const [statsData, topReposData, timeseriesResult, quotaData] =
      await Promise.all([
        getDetailedStats(adminStore.token),
        getTopRepositories(adminStore.token, 5, "commits"),
        getTimeseriesStats(adminStore.token, chartDays.value),
        getQuotaOverview(adminStore.token),
      ]);

    stats.value = statsData;
    topRepos.value = topReposData.top_repositories;
    timeseriesData.value = timeseriesResult;
    quotaOverview.value = quotaData;
  } catch (error) {
    console.error("Failed to load stats:", error);
    if (error.response?.status === 401 || error.response?.status === 403) {
      ElMessage.error("Invalid admin token. Please login again.");
      adminStore.logout();
      router.push("/login");
    } else {
      ElMessage.error(
        error.response?.data?.detail?.error || "Failed to load system stats",
      );
    }
  } finally {
    loading.value = false;
  }
}

// Computed chart data for user growth
const userGrowthChart = computed(() => {
  if (!timeseriesData.value) return null;

  const dates = Object.keys(timeseriesData.value.users_by_day).sort();
  const values = dates.map((date) => timeseriesData.value.users_by_day[date]);

  return {
    labels: dates,
    datasets: [
      {
        label: "New Users",
        data: values,
        borderColor: "#409EFF",
        backgroundColor: "rgba(64, 158, 255, 0.1)",
        fill: true,
        tension: 0.4,
      },
    ],
  };
});

// Computed chart data for repository growth
const repoGrowthChart = computed(() => {
  if (!timeseriesData.value) return null;

  const dates = Object.keys(timeseriesData.value.repositories_by_day).sort();
  const modelData = dates.map(
    (date) => timeseriesData.value.repositories_by_day[date]?.model || 0,
  );
  const datasetData = dates.map(
    (date) => timeseriesData.value.repositories_by_day[date]?.dataset || 0,
  );
  const spaceData = dates.map(
    (date) => timeseriesData.value.repositories_by_day[date]?.space || 0,
  );

  return {
    labels: dates,
    datasets: [
      {
        label: "Models",
        data: modelData,
        borderColor: "#409EFF",
        backgroundColor: "rgba(64, 158, 255, 0.1)",
        fill: true,
      },
      {
        label: "Datasets",
        data: datasetData,
        borderColor: "#67C23A",
        backgroundColor: "rgba(103, 194, 58, 0.1)",
        fill: true,
      },
      {
        label: "Spaces",
        data: spaceData,
        borderColor: "#E6A23C",
        backgroundColor: "rgba(230, 162, 60, 0.1)",
        fill: true,
      },
    ],
  };
});

// Computed chart data for commit activity
const commitActivityChart = computed(() => {
  if (!timeseriesData.value) return null;

  const dates = Object.keys(timeseriesData.value.commits_by_day).sort();
  const values = dates.map((date) => timeseriesData.value.commits_by_day[date]);

  return {
    labels: dates,
    datasets: [
      {
        label: "Commits",
        data: values,
        borderColor: "#F56C6C",
        backgroundColor: "rgba(245, 108, 108, 0.1)",
        fill: true,
        tension: 0.4,
      },
    ],
  };
});

function getRepoTypeColor(type) {
  switch (type) {
    case "model":
      return "primary";
    case "dataset":
      return "success";
    case "space":
      return "warning";
    default:
      return "info";
  }
}

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.page-container {
  padding: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

/* Enhanced card styling */
:deep(.el-card) {
  background-color: var(--bg-card);
  border-color: var(--border-default);
  transition: all 0.3s ease;
  border-radius: 12px;
}

:deep(.el-card:hover) {
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}

:deep(.el-card__header) {
  background-color: var(--bg-hover);
  border-bottom-color: var(--border-default);
  padding: 16px 20px;
}

:deep(.el-card__header .font-bold) {
  color: var(--text-primary);
  font-size: 15px;
}

/* Table styling */
:deep(.el-table) {
  background-color: var(--bg-card);
}

:deep(.el-table th) {
  background-color: var(--bg-hover);
  color: var(--text-primary);
  font-weight: 600;
  border-color: var(--border-default);
}

:deep(.el-table td) {
  color: var(--text-primary);
  border-color: var(--border-light);
}

:deep(.el-table__body tr:hover > td) {
  background-color: var(--bg-hover) !important;
}

/* Warning colors */
:deep(.text-red-600) {
  color: var(--color-error) !important;
  font-weight: 700;
}

:deep(.text-sm.text-gray-500) {
  color: var(--text-secondary);
}
</style>
