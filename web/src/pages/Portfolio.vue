<script setup>
import { ref, computed } from "vue";

// 狀態控制
const loading = ref(false);

const totalAssets = ref(1250000);
const totalUnrealized = ref(45800);
const totalReturnRate = ref(3.65);
const realizedDay = ref(1200);

// 貨幣格式化
const formatCurrency = value => {
	return new Intl.NumberFormat("zh-TW", {
		stype: "currency",
		currency: "TWD",
		maximumFractionDigits: 0,
	}).format(value);
};

// 手動更新
const refreshData = () => {
	loading.value = true;
	setTimeout(() => {
		loading.value = false;
	}, 1000);
};
</script>

<template>
	<div class="min-h-screen bg-slate-900 text-slate-100 p-6">
		<!-- 頂部標題 -->
		<div>
			<h1 class="text-2xl font-bold">股票帳務</h1>
			<p class="text-slate-400 text-sm">現貨資產狀態</p>
		</div>

		<button
			@click="refreshData"
			class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors disabled:opacity-50"
			:disabled="loading"
		>
			<span v-if="loading">讀取中...</span>
			<span v-else>刷新報價</span>
		</button>
	</div>
	<!-- 頂部 -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
		<!-- 總權益數 -->
		<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
			<h3 class="text-slate-400 text-sm mb-2">總權益數 (Est.)</h3>
			<div class="text-mono font-bold text-white">
				{{ formatCurrency(totalAssets) }}
			</div>
		</div>
		<!-- 未實現損益 -->
		<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
			<h3 class="">未實現損益</h3>
			<div
				class="text-2xl font-mono font-bold"
				:class="totalUnrealized >= 0 ? 'text-red-500' : 'text-green-500'"
			>
				{{ totalUnrealized >= 0 ? "+" : ""
				}}{{ formatCurrency(totalUnrealized) }}
			</div>
		</div>
	</div>
</template>
