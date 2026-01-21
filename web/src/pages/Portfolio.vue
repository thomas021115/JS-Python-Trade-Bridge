<script setup>
import { ref, computed } from "vue";

// 狀態控制
const loading = ref(false);

const totalAssets = ref(1250000);
const totalUnrealized = ref(45800);
const totalReturnRate = ref(3.65);
const realizedDay = ref(1200);
const activeTab = ref("positions"); // 'positions' | 'accounting'

const positions = ref([
	{
		code: "2330",
		name: "台積電",
		quantity: 2000, // 2張
		price: 580.5, // 平均成本
		current_price: 1030, // 目前市價
		pnl: 899000, // 未實現損益 (模擬算好的)
		pnl_rate: 77.43, // 報酬率 (%)
	},
	{
		code: "2603",
		name: "長榮",
		quantity: 5000,
		price: 185.0,
		current_price: 170.5,
		pnl: -72500,
		pnl_rate: -7.83,
	},
]);

// 貨幣格式化
const formatCurrency = value => {
	return new Intl.NumberFormat("zh-TW", {
		style: "currency",
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
				<span>{{ totalReturnRate }}%</span>
			</div>
		</div>

		<!-- 今日已實現 -->
		<div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
			<h3 class="text-slate-400 text-sm mb-2">今日已實現</h3>
			<div
				class="text-2xl font-mono font-bold"
				:class="realizedDay >= 0 ? 'text-red-400' : 'text-slate-100'"
			>
				{{ formatCurrency(realizedDay) }}
			</div>
		</div>
	</div>

	<!-- 分頁標籤 -->
	<div
		class="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden mt-8"
	>
		<div class="flex border-b border-slate-700">
			<button
				@click="activeTab = 'positions'"
				class="px-6 py-4 text-sm font-medium transition-colors"
				:class="
					activeTab === 'positions'
						? 'text-blue-400 border-b-2 border-blue-400 bg-slate-700/50'
						: 'text-slate-400 hover:text-white'
				"
			>
				庫存部位
			</button>
			<button
				@click="activeTab = 'accounting'"
				class="px-6 py-4 text-sm font-medium transition-colors"
				:class="
					activeTab === 'accounting'
						? 'text-blue-400 border-b-2 border-blue-400 bg-slate-700/50'
						: 'text-slate-400 hover:text-white'
				"
			>
				帳務明細 (Coming Soon)
			</button>
		</div>
	</div>
	<div v-if="activeTab === 'positions'" class="overflow-x-auto">
		<table>
			<thead>
				<tr>
					<th class="text-left p-4">股票代碼</th>
					<th class="text-left p-4">名稱</th>
					<th class="text-left p-4">股數</th>
					<th class="text-left p-4">平均成本</th>
					<th class="text-left p-4">目前市價</th>
					<th class="text-left p-4">未實現損益</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(position, index) in positions" :key="index">
					<td class="p-4">{{ position.code }}</td>
					<td class="p-4">{{ position.name }}</td>
					<td class="p-4">{{ position.quantity }}</td>
					<td class="p-4">{{ formatCurrency(position.price) }}</td>
					<td class="p-4">{{ formatCurrency(position.current_price) }}</td>
					<td
						class="p-4"
						:class="position.pnl >= 0 ? 'text-red-500' : 'text-green-500'"
					>
						{{ formatCurrency(position.pnl) }}
						({{ position.pnl_rate }}%)
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>
