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
	return new Intl.NumberFormate("zh-TW", {
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
	<div class="min-h-screen g-slate-900 text-slate-100 p-6">
		<!-- 頂部導航 -->
		<div class="">
			<h1>股票帳務</h1>
			<p>現貨資產狀態</p>
		</div>

		<button @click="refeshData" :disabled="loading">
			<span v-if="loading">讀取中...</span>
			<span v-else>刷新報價</span>
		</button>
	</div>
</template>
