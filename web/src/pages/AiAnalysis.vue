<script setup lang="ts">
import { ref } from 'vue';
import { api } from '@/services/api';
import type { AiReportResponse } from '@/services/api';
import { downloadMarkdown, buildReportFilename } from '@/utils/download';
import { toast } from 'vue3-toastify';

// Layout shell: page background + centered container (shared across pages)
import PageShell from '@/components/layout/PageShell.vue';
// UI primitive: reusable card surface (rounded / shadow / padding)
import AppCard from '@/components/ui/AppCard.vue';

const symbol = ref('2330');

const report = ref<AiReportResponse | null>(null);

const loadingReport = ref(false);

const errorMsg = ref<string | null>(null);

console.log('[init]', {
	symbol: symbol.value,
	report: report.value,
});

async function fetchReport() {
	console.log('[door] fetchReport called');

	loadingReport.value = true;
	errorMsg.value = null;

	try {
		console.log('[before api]');
		const res = await api.getAiReport(symbol.value);
		console.log('[after] res', res);

		if (res.error) {
			errorMsg.value = res.error;
			toast.error(errorMsg.value);
			console.log('[res.error]', res.error);
			return;
		}
		report.value = res;
		console.log('[res.error]', res.report?.length);

		const filename = buildReportFilename(res.code);
		downloadMarkdown(filename, res.report ?? '');

		toast.success('下載完成');
	} catch (err) {
		errorMsg.value = '抓取資料失敗 (console / Network)';
		toast.error(errorMsg.value);
		console.log('[catch error]', err);
	} finally {
		loadingReport.value = false;
		console.log('[finally] loadingReport=false');
	}
}
</script>

<template>
	<PageShell>
		<AppCard>
			<div class="flex items-start justify-between">
				<div>
					<h1 class="text-2xl font-bold tracking-tight text-slate-900">
						AI 戰報生成器
					</h1>
					<p class="text-sm text-slate-500 mt-2 leading-relaxed">
						輸入股票代碼，即時連線 Python 後端計算指標，<br />
						並自動下載 AI 分析報告。
					</p>
				</div>

				<span
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors duration-300"
					:class="
						loadingReport
							? 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20'
							: 'bg-slate-100 text-slate-600 ring-1 ring-slate-500/10'
					"
				>
					<span class="relative flex h-2 w-2">
						<span
							v-if="loadingReport"
							class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"
						></span>
						<span
							class="relative inline-flex rounded-full h-2 w-2"
							:class="loadingReport ? 'bg-blue-500' : 'bg-slate-400'"
						></span>
					</span>
					{{ loadingReport ? '下載中...' : '' }}
				</span>
			</div>

			<div class="space-y-4">
				<label class="block text-sm font-medium text-slate-700">股票代碼</label>

				<div class="flex gap-3">
					<div class="relative flex-1 group">
						<div
							class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
						>
							<span class="text-slate-400 text-sm font-mono">TW.</span>
						</div>
						<input
							v-model="symbol"
							type="text"
							inputmode="numeric"
							placeholder="2330"
							@keydown.enter="!loadingReport ? fetchReport() : null"
							class="block w-full rounded-xl border-0 py-3 pl-12 pr-4 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
						/>
					</div>

					<button
						@click="fetchReport"
						:disabled="loadingReport"
						class="shrink-0 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
					>
						<svg
							v-if="loadingReport"
							class="animate-spin -ml-1 h-4 w-4 text-white"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						<span v-else>
							<svg
								class="w-4 h-4"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
								></path>
							</svg>
						</span>
						{{ loadingReport ? '處理中' : '下載報告' }}
					</button>
				</div>
			</div>

			<div
				v-if="errorMsg"
				class="rounded-lg bg-red-50 p-4 border border-red-100 flex gap-3"
			>
				<div class="shrink-0 text-red-500">
					<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<div class="text-sm text-red-700">
					<h3 class="font-medium">連線失敗</h3>
					<p class="mt-1 opacity-90">{{ errorMsg }}</p>
				</div>
			</div>

			<div class="rounded-xl bg-slate-50/50 ring-1 ring-slate-200 p-5">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-sm font-semibold text-slate-900">執行狀態</h3>
					<span class="text-xs font-mono text-slate-500">{{
						report ? 'SUCCESS' : 'IDLE'
					}}</span>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div class="p-3 bg-white rounded-lg shadow-sm ring-1 ring-slate-100">
						<div
							class="text-xs text-slate-500 font-medium uppercase tracking-wider"
						>
							Target
						</div>
						<div class="mt-1 text-lg font-bold text-slate-900 font-mono">
							{{ symbol }}
						</div>
					</div>
					<div class="p-3 bg-white rounded-lg shadow-sm ring-1 ring-slate-100">
						<div
							class="text-xs text-slate-500 font-medium uppercase tracking-wider"
						>
							Report Length
						</div>
						<div class="mt-1 text-lg font-bold text-slate-900 font-mono">
							{{ report?.report ? report.report.length + ' chars' : '-' }}
						</div>
					</div>
				</div>
			</div>

			<div class="border-t border-slate-100 pt-6 text-center">
				<p class="text-xs text-slate-400">
					JS-Python-Trade-Bridge v1.0 • Power by FastAPI & Vue 3
				</p>
			</div>
		</AppCard>
	</PageShell>
</template>
