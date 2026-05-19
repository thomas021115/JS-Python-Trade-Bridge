<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api, type StockPosition } from "@/services/api";

const loading = ref(false);
const errorMsg = ref<string | null>(null);
const positions = ref<StockPosition[]>([]);
const symbols = ref<string[]>([]);
const activeTab = ref<"positions" | "accounting">("positions");

const positionCount = computed(() => positions.value.length);
const totalMarketValue = computed(() =>
	positions.value.reduce((sum, pos) => sum + pos.market_value, 0),
);
const totalUnrealized = computed(() =>
	positions.value.reduce((sum, pos) => sum + pos.pnl, 0),
);
const totalCost = computed(() =>
	positions.value.reduce((sum, pos) => sum + pos.quantity * pos.price, 0),
);
const totalReturnRate = computed(() =>
	totalCost.value ? (totalUnrealized.value / totalCost.value) * 100 : 0,
);

const formatCurrency = (value: number) => {
	return new Intl.NumberFormat("zh-TW", {
		style: "currency",
		currency: "TWD",
		maximumFractionDigits: 0,
	}).format(value);
};

const formatNumber = (value: number) => {
	return new Intl.NumberFormat("zh-TW").format(value);
};

const formatPercent = (value: number) => {
	return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const refreshData = async () => {
	loading.value = true;
	errorMsg.value = null;

	try {
		const res = await api.getStockPositions();

		if (!res.success) {
			errorMsg.value = res.error || "讀取 Shioaji 庫存失敗";
			positions.value = [];
			symbols.value = [];
			return;
		}

		positions.value = res.positions ?? [];
		symbols.value = res.symbols ?? positions.value.map((pos) => pos.code);
	} catch (err) {
		console.error("[portfolio.refresh]", err);
		errorMsg.value = "無法連線到後端 API，請確認 FastAPI 已啟動";
		positions.value = [];
		symbols.value = [];
	} finally {
		loading.value = false;
	}
};

const analyzeStock = (code: string) => {
	console.log("[analyze]", code);
};

onMounted(() => {
	refreshData();
});
</script>

<template>
	<main class="min-h-screen bg-slate-950 text-slate-100">
		<section class="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
			<header class="flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-end md:justify-between">
				<div>
					<h1 class="text-2xl font-bold tracking-tight">Shioaji 帳戶庫存</h1>
					<p class="mt-2 text-sm text-slate-400">
						目前持有 {{ positionCount }} 檔股票
					</p>
				</div>

				<button
					@click="refreshData"
					:disabled="loading"
					class="inline-flex items-center justify-center rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
				>
					{{ loading ? "讀取中..." : "重新整理" }}
				</button>
			</header>

			<div v-if="errorMsg" class="rounded-lg border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
				{{ errorMsg }}
			</div>

			<section class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-slate-800 bg-slate-900 p-5">
					<div class="text-sm text-slate-400">股票檔數</div>
					<div class="mt-2 text-3xl font-bold">{{ positionCount }}</div>
					<div class="mt-3 text-sm text-slate-500">
						{{ symbols.length ? symbols.join(", ") : "尚無庫存" }}
					</div>
				</div>

				<div class="rounded-lg border border-slate-800 bg-slate-900 p-5">
					<div class="text-sm text-slate-400">庫存市值</div>
					<div class="mt-2 text-3xl font-bold">{{ formatCurrency(totalMarketValue) }}</div>
				</div>

				<div class="rounded-lg border border-slate-800 bg-slate-900 p-5">
					<div class="text-sm text-slate-400">未實現損益</div>
					<div
						class="mt-2 text-3xl font-bold"
						:class="totalUnrealized >= 0 ? 'text-red-400' : 'text-emerald-400'"
					>
						{{ totalUnrealized >= 0 ? "+" : "" }}{{ formatCurrency(totalUnrealized) }}
					</div>
					<div
						class="mt-2 text-sm font-medium"
						:class="totalReturnRate >= 0 ? 'text-red-300' : 'text-emerald-300'"
					>
						{{ formatPercent(totalReturnRate) }}
					</div>
				</div>
			</section>

			<section class="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
				<div class="flex border-b border-slate-800">
					<button
						@click="activeTab = 'positions'"
						class="px-5 py-3 text-sm font-medium transition"
						:class="activeTab === 'positions' ? 'border-b-2 border-sky-400 text-sky-300' : 'text-slate-400 hover:text-slate-100'"
					>
						庫存明細
					</button>
					<button
						@click="activeTab = 'accounting'"
						class="px-5 py-3 text-sm font-medium transition"
						:class="activeTab === 'accounting' ? 'border-b-2 border-sky-400 text-sky-300' : 'text-slate-400 hover:text-slate-100'"
					>
						帳務資訊
					</button>
				</div>

				<div v-if="activeTab === 'positions'" class="overflow-x-auto">
					<table class="w-full min-w-[900px] text-left text-sm">
						<thead class="bg-slate-950/70 text-slate-400">
							<tr>
								<th class="px-4 py-3 font-medium">股票</th>
								<th class="px-4 py-3 text-right font-medium">方向</th>
								<th class="px-4 py-3 text-right font-medium">股數</th>
								<th class="px-4 py-3 text-right font-medium">均價</th>
								<th class="px-4 py-3 text-right font-medium">現價</th>
								<th class="px-4 py-3 text-right font-medium">市值</th>
								<th class="px-4 py-3 text-right font-medium">未實現損益</th>
								<th class="px-4 py-3 text-center font-medium">操作</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-800">
							<tr v-for="pos in positions" :key="`${pos.code}-${pos.id}`" class="hover:bg-slate-800/50">
								<td class="px-4 py-3">
									<div class="font-semibold text-slate-100">{{ pos.name || pos.code }}</div>
									<div class="text-xs text-slate-500">{{ pos.code }}</div>
								</td>
								<td class="px-4 py-3 text-right text-slate-300">{{ pos.direction || "-" }}</td>
								<td class="px-4 py-3 text-right font-mono">{{ formatNumber(pos.quantity) }}</td>
								<td class="px-4 py-3 text-right font-mono">{{ pos.price.toFixed(2) }}</td>
								<td class="px-4 py-3 text-right font-mono">{{ pos.last_price.toFixed(2) }}</td>
								<td class="px-4 py-3 text-right font-mono">{{ formatCurrency(pos.market_value) }}</td>
								<td class="px-4 py-3 text-right font-mono">
									<div :class="pos.pnl >= 0 ? 'text-red-400' : 'text-emerald-400'">
										{{ pos.pnl >= 0 ? "+" : "" }}{{ formatCurrency(pos.pnl) }}
									</div>
									<div class="text-xs" :class="pos.pnl_rate >= 0 ? 'text-red-300' : 'text-emerald-300'">
										{{ formatPercent(pos.pnl_rate) }}
									</div>
								</td>
								<td class="px-4 py-3 text-center">
									<button
										@click="analyzeStock(pos.code)"
										class="rounded-md border border-sky-400/40 px-3 py-1 text-xs font-medium text-sky-300 transition hover:bg-sky-400/10"
									>
										AI 分析
									</button>
								</td>
							</tr>
						</tbody>
					</table>

					<div v-if="!loading && positions.length === 0" class="px-4 py-10 text-center text-sm text-slate-500">
						目前沒有股票庫存
					</div>
				</div>

				<div v-else class="px-4 py-10 text-center text-sm text-slate-500">
					帳務資訊之後可接 Shioaji balance / settlement API
				</div>
			</section>
		</section>
	</main>
</template>
