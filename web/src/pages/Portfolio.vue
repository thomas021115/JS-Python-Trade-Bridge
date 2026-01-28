<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
const router = useRouter();

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
		quantity: 2000, // 股數
		price: 580.5, // 平均成本
		current_price: 1030, // 目前市價
		pnl: 899000, // 未實現損益
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
const formatCurrency = (value: number) => {
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

const analyzeStock = (code: string) => {
	router.push({ path: "/", query: { code: code } });
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

		<!-- 頂部 -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<!-- 總權益數 -->
			<div
				class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg"
			>
				<h3 class="text-slate-400 text-sm mb-2">總權益數 (Est.)</h3>
				<div class="text-mono font-bold text-white">
					{{ formatCurrency(totalAssets) }}
				</div>
			</div>

			<!-- 未實現損益 -->
			<div
				class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg"
			>
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
			<div
				class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg"
			>
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
			<table class="w-full text-left border-collapse">
				<thead>
					<tr class="bg-slate-700/50 text-sm">
						<th class="p-4 font-medium">商品</th>
						<th class="p-4 font-medium text-right">庫存</th>
						<th class="p-4 font-medium text-right">均價 / 現價</th>
						<th class="p-4 font-medium text-right">市值</th>
						<th class="p-4 font-medium text-right">損益 (%)</th>
						<th class="p-4 font-medium text-center">AI分析</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-700 text-sm">
					<tr
						v-for="pos in positions"
						:key="pos.code"
						class="hover:bg-slate-700/30 active:bg-slate-700/50 transition-colors cursor-pointer"
					>
						<!-- 商品 -->
						<td class="p-4">
							<div class="font-bold text-white">{{ pos.name }}</div>
							<div class="text-xs text-slate-500">{{ pos.code }}</div>
						</td>

						<!-- 庫存 -->
						<td class="p-4 text-right font-mono text-white">
							{{ pos.quantity }}
						</td>

						<!-- 均價 / 現價 -->
						<td class="p-4 text-right">
							<div class="font-mono text-white">{{ pos.current_price }}</div>
							<div class="text-xs text-slate-500">成本: {{ pos.price }}</div>
						</td>

						<!-- 市值 -->
						<td class="p-4 text-right font-mono text-slate-300">
							{{ formatCurrency(pos.quantity * pos.current_price) }}
						</td>

						<!-- 損益 (紅漲綠跌邏輯) -->
						<td class="p-4 text-right font-mono font-bold">
							<div :class="pos.pnl >= 0 ? 'text-red-500' : 'text-green-500'">
								{{ pos.pnl >= 0 ? "+" : "" }}{{ formatCurrency(pos.pnl) }}
							</div>
							<div
								:class="pos.pnl_rate >= 0 ? 'text-red-500' : 'text-green-500'"
								class="text-xs"
							>
								{{ pos.pnl_rate }}%
							</div>
						</td>

						<!-- 操作按鈕 -->
						<td class="p-4 text-center">
							<button
								@click="analyzeStock(pos.code)"
								class="px-3 py-1 bg-indigo-500/20 text-indigo-300 border border-indigo-500/50 rounded hover:bg-indigo-500/40 transition-colors text-xs"
							>
								分析走勢
							</button>
						</td>
					</tr>
				</tbody>
			</table>

			<!-- 無資料時的提示 -->
			<div v-if="positions.length === 0" class="p-8 text-center text-slate-500">
				目前沒有持倉
			</div>
		</div>
	</div>
</template>
