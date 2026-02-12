<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// 狀態控制
const router = useRouter();
const loading = ref(false);

// === 假資料區域 Start ===
const totalAssets = ref(1250000);
const totalUnrealized = ref(45800);
const totalReturnRate = ref(3.65);
const realizedDay = ref(1200);
const activeTab = ref('positions'); // 'positions' | 'accounting'

const positions = ref([
	{
		code: '2330',
		name: '台積電',
		quantity: 2000, // 股數
		price: 580.5, // 平均成本
		current_price: 1030, // 目前市價
		pnl: 899000, // 未實現損益
		pnl_rate: 77.43, // 報酬率 (%)
	},
	{
		code: '2603',
		name: '長榮',
		quantity: 5000,
		price: 185.0,
		current_price: 170.5,
		pnl: -72500,
		pnl_rate: -7.83,
	},
]);
// === 假資料區域 End ===

// 貨幣格式化 (台幣 $1,234)
const formatCurrency = (value: number) => {
	return new Intl.NumberFormat('zh-TW', {
		style: 'currency',
		currency: 'TWD',
		maximumFractionDigits: 0,
	}).format(value);
};

// 手動更新 (模擬)
const refreshData = () => {
	loading.value = true;
	setTimeout(() => {
		loading.value = false;
	}, 1000);
};

// 跳轉到 AI 分析頁
const analyzeStock = (code: string) => {
	router.push({ path: '/aianalysis', query: { code: code } });
};
</script>

<template>
	<div class="min-h-full bg-slate-50 text-slate-900 p-6 rounded-xl">
		<div class="flex justify-between items-center mb-8">
			<div>
				<h1 class="text-2xl font-bold text-slate-900">股票帳務</h1>
				<p class="text-slate-500 text-sm">現貨資產狀態</p>
			</div>

			<button
				@click="refreshData"
				class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 text-sm font-medium shadow-sm"
				:disabled="loading"
			>
				<span v-if="loading">讀取中...</span>
				<span v-else>刷新報價</span>
			</button>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
				<h3 class="text-slate-500 text-sm font-medium mb-2">總權益數 (Est.)</h3>
				<div class="text-2xl font-mono font-bold text-slate-900">
					{{ formatCurrency(totalAssets) }}
				</div>
			</div>

			<div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
				<h3 class="text-slate-500 text-sm font-medium mb-2">未實現損益</h3>
				<div
					class="text-2xl font-mono font-bold flex items-baseline gap-2"
					:class="totalUnrealized >= 0 ? 'text-red-600' : 'text-green-600'"
				>
					<span
						>{{ totalUnrealized >= 0 ? '+' : ''
						}}{{ formatCurrency(totalUnrealized) }}</span
					>
					<span
						class="text-sm px-2 py-0.5 rounded font-medium"
						:class="
							totalUnrealized >= 0
								? 'bg-red-50 text-red-600'
								: 'bg-green-50 text-green-600'
						"
					>
						{{ totalReturnRate }}%
					</span>
				</div>
			</div>

			<div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
				<h3 class="text-slate-500 text-sm font-medium mb-2">今日已實現</h3>
				<div
					class="text-2xl font-mono font-bold"
					:class="realizedDay >= 0 ? 'text-red-600' : 'text-slate-900'"
				>
					{{ formatCurrency(realizedDay) }}
				</div>
			</div>
		</div>

		<div class="bg-white rounded-t-xl border-b border-slate-200 mt-8">
			<div class="flex">
				<button
					@click="activeTab = 'positions'"
					class="px-6 py-4 text-sm font-medium transition-colors border-b-2"
					:class="
						activeTab === 'positions'
							? 'text-blue-600 border-blue-600 bg-blue-50/50'
							: 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
					"
				>
					庫存部位
				</button>
				<button
					@click="activeTab = 'accounting'"
					class="px-6 py-4 text-sm font-medium transition-colors border-b-2"
					:class="
						activeTab === 'accounting'
							? 'text-blue-600 border-blue-600 bg-blue-50/50'
							: 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
					"
				>
					帳務明細 (Coming Soon)
				</button>
			</div>
		</div>

		<div
			v-if="activeTab === 'positions'"
			class="overflow-x-auto bg-white rounded-b-xl border border-slate-200 border-t-0 shadow-sm"
		>
			<table class="w-full text-left border-collapse">
				<thead>
					<tr
						class="bg-slate-50 text-sm text-slate-500 border-b border-slate-200"
					>
						<th class="p-4 font-medium">商品</th>
						<th class="p-4 font-medium text-right">庫存</th>
						<th class="p-4 font-medium text-right">均價 / 現價</th>
						<th class="p-4 font-medium text-right">市值</th>
						<th class="p-4 font-medium text-right">損益 (%)</th>
						<th class="p-4 font-medium text-center">操作</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100 text-sm">
					<tr
						v-for="pos in positions"
						:key="pos.code"
						class="hover:bg-slate-50 transition-colors"
					>
						<td class="p-4">
							<div class="font-bold text-slate-900 text-lg">{{ pos.name }}</div>
							<div
								class="text-xs text-slate-500 bg-slate-100 inline-block px-1.5 py-0.5 rounded mt-1"
							>
								{{ pos.code }}
							</div>
						</td>

						<td class="p-4 text-right font-mono text-slate-900 text-base">
							{{ pos.quantity }}
						</td>

						<td class="p-4 text-right">
							<div class="font-mono text-slate-900">
								{{ pos.current_price }}
							</div>
							<div class="text-xs text-slate-500 mt-1">
								成本: {{ pos.price }}
							</div>
						</td>

						<td class="p-4 text-right font-mono text-slate-600">
							{{ formatCurrency(pos.quantity * pos.current_price) }}
						</td>

						<td class="p-4 text-right font-mono font-bold">
							<div
								:class="pos.pnl >= 0 ? 'text-red-600' : 'text-green-600'"
								class="text-base"
							>
								{{ pos.pnl >= 0 ? '+' : '' }}{{ formatCurrency(pos.pnl) }}
							</div>
							<div
								:class="pos.pnl_rate >= 0 ? 'text-red-600' : 'text-green-600'"
								class="text-xs mt-1"
							>
								{{ pos.pnl_rate }}%
							</div>
						</td>

						<td class="p-4 text-center">
							<button
								@click="analyzeStock(pos.code)"
								class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs transition-colors shadow-sm font-medium"
							>
								AI 分析
							</button>
						</td>
					</tr>
				</tbody>
			</table>

			<div
				v-if="positions.length === 0"
				class="p-12 text-center text-slate-500"
			>
				目前沒有持倉
			</div>
		</div>
	</div>
</template>
