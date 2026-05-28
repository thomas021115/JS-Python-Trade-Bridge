<script setup lang="ts">
import { computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import PageShell from '@/components/layout/PageShell.vue';
import AppCard from '@/components/ui/AppCard.vue';
import { useReport } from '@/stores/report';

const s = useReport();
const {
  symbol,
  startDate,
  endDate,
  report,
  loadingReport,
  errorMsg,
  syncing,
  syncResult,
  syncErrorMsg,
} = storeToRefs(s);

const reportText = computed(() => report.value?.report?.trim() ?? '');
const hasReport = computed(() => reportText.value.length > 0);
const dataSource = computed(() => report.value?.data_source ?? report.value?.source ?? '-');
const isBusy = computed(() => loadingReport.value || syncing.value);
const dataQualityWarning = computed(() => Boolean(report.value?.data_quality_warning));
const dataQualityMessage = computed(() => report.value?.message ?? '資料不足，請先同步資料');
const statusLabel = computed(() => {
  if (syncing.value) return '同步中';
  if (loadingReport.value) return '產生中';
  if (errorMsg.value || syncErrorMsg.value) return '需要確認';
  if (hasReport.value) return '資料包完成';
  return '待命';
});
const statusTone = computed(() => {
  if (syncing.value || loadingReport.value) return 'border-sky-300/40 bg-sky-400/10 text-sky-200';
  if (errorMsg.value || syncErrorMsg.value) return 'border-rose-300/40 bg-rose-400/10 text-rose-200';
  if (hasReport.value) return 'border-emerald-300/40 bg-emerald-400/10 text-emerald-200';
  return 'border-amber-300/30 bg-amber-300/10 text-amber-100';
});
const syncStats = computed(() => [
  ['Fetched Rows', syncResult.value?.fetched_rows],
  ['Saved 1m Rows', syncResult.value?.saved_1m_rows],
  ['Saved 1d Rows', syncResult.value?.saved_1d_rows],
  ['Saved 1w Rows', syncResult.value?.saved_1w_rows],
  ['Snapshot 1d', syncResult.value?.technical_snapshot_1d_saved],
  ['Snapshot 1w', syncResult.value?.technical_snapshot_1w_saved],
  ['Elapsed Seconds', syncResult.value?.elapsed_seconds],
]);

watch([symbol, startDate, endDate], () => {
  errorMsg.value = null;
  syncErrorMsg.value = null;
  report.value = null;
  syncResult.value = null;
});

function validateForm(target: 'report' | 'sync') {
  const code = symbol.value.trim();
  let message = '';

  if (!code) {
    message = '請輸入股票代號';
  } else if (!/^\d{4,6}$/.test(code)) {
    message = '股票代號格式不正確，請輸入 4 到 6 位數字';
  } else if (!startDate.value || !endDate.value) {
    message = '請選擇開始日期與結束日期';
  } else if (startDate.value > endDate.value) {
    message = '開始日期不能晚於結束日期';
  }

  if (message) {
    if (target === 'sync') {
      syncErrorMsg.value = message;
    } else {
      errorMsg.value = message;
    }
    return false;
  }

  symbol.value = code;
  return true;
}

function fetchReport() {
  if (!validateForm('report')) return;
  return s.fetchreport();
}

function syncData() {
  if (!validateForm('sync')) return;
  return s.syncData();
}
</script>

<template>
  <PageShell theme="aurum" variant="wide" outer-class="py-8 sm:py-12">
    <AppCard tone="aurum">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.28em] text-amber-200/70">
            AI Research Packet
          </p>
          <h1 class="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            AI 技術分析資料包
          </h1>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
            先同步指定區間資料，再從資料庫產生 Markdown 資料包。同步資料會呼叫 Shioaji，建議盤後或短區間使用，單次最多 30 天。
          </p>
        </div>

        <div
          class="inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold"
          :class="statusTone"
        >
          <span
            class="h-2 w-2 rounded-full"
            :class="syncing || loadingReport ? 'animate-pulse bg-sky-300' : 'bg-amber-200'"
          />
          {{ statusLabel }}
        </div>
      </div>

      <div class="mt-8 grid gap-6 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <section class="rounded-xl border border-amber-300/20 bg-slate-950/70 p-5 shadow-lg shadow-black/20">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-white">查詢條件</h2>
              <p class="mt-1 text-xs text-slate-400">股票代號與資料區間</p>
            </div>
            <span class="font-mono text-xs text-amber-200/80">TWSE</span>
          </div>

          <div class="mt-5 space-y-4">
            <label class="block text-xs font-medium uppercase tracking-wider text-slate-400">
              股票代號
              <div class="group relative mt-2">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <span class="font-mono text-sm text-amber-200/70">TW.</span>
                </div>
                <input
                  v-model.trim="symbol"
                  type="text"
                  inputmode="numeric"
                  placeholder="2330"
                  :disabled="isBusy"
                  class="block w-full rounded-lg border border-slate-700 bg-slate-900/90 py-3 pl-12 pr-4 font-mono text-sm text-white shadow-inner outline-none transition placeholder:text-slate-600 focus:border-amber-300 focus:ring-2 focus:ring-amber-300/25 disabled:cursor-not-allowed disabled:opacity-50"
                  @keydown.enter="!isBusy ? fetchReport() : null"
                />
              </div>
            </label>

            <div class="grid gap-3 sm:grid-cols-2">
              <label class="block text-xs font-medium uppercase tracking-wider text-slate-400">
                開始日期
                <input
                  v-model="startDate"
                  type="date"
                  :disabled="isBusy"
                  class="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-900/90 px-4 py-3 font-mono text-sm text-white outline-none transition focus:border-amber-300 focus:ring-2 focus:ring-amber-300/25 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </label>

              <label class="block text-xs font-medium uppercase tracking-wider text-slate-400">
                結束日期
                <input
                  v-model="endDate"
                  type="date"
                  :disabled="isBusy"
                  class="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-900/90 px-4 py-3 font-mono text-sm text-white outline-none transition focus:border-amber-300 focus:ring-2 focus:ring-amber-300/25 disabled:cursor-not-allowed disabled:opacity-50"
                  @keydown.enter="!isBusy ? fetchReport() : null"
                />
              </label>
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                :disabled="isBusy"
                class="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-300 to-yellow-500 px-5 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-amber-950/30 transition hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
                @click="fetchReport"
              >
                <span
                  v-if="loadingReport"
                  class="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950"
                />
                <span v-else class="font-mono">MD</span>
                {{ loadingReport ? '產生中...' : '產生資料包' }}
              </button>

              <button
                type="button"
                :disabled="isBusy"
                class="inline-flex items-center justify-center gap-2 rounded-lg border border-amber-300/45 bg-slate-950 px-5 py-3 text-sm font-semibold text-amber-100 shadow-lg shadow-black/20 transition hover:border-amber-200 hover:bg-amber-300/10 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
                @click="syncData"
              >
                <span
                  v-if="syncing"
                  class="h-4 w-4 animate-spin rounded-full border-2 border-amber-200/30 border-t-amber-200"
                />
                <span v-else class="font-mono">SYNC</span>
                {{ syncing ? '同步中...' : '同步資料' }}
              </button>
            </div>
          </div>

          <div
            v-if="dataQualityWarning"
            class="mt-5 rounded-lg border border-amber-300/35 bg-amber-300/10 p-4 text-sm text-amber-100"
          >
            <div class="font-semibold">資料不足，請先同步資料</div>
            <p class="mt-1 text-amber-100/80">{{ dataQualityMessage }}</p>
          </div>

          <div
            v-if="errorMsg || syncErrorMsg"
            class="mt-5 rounded-lg border border-rose-300/35 bg-rose-400/10 p-4 text-sm text-rose-100"
          >
            <div class="font-semibold">操作未完成</div>
            <p class="mt-1 text-rose-100/80">{{ errorMsg || syncErrorMsg }}</p>
          </div>
        </section>

        <section class="grid gap-4 sm:grid-cols-2">
          <div class="rounded-xl border border-amber-300/20 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Target</div>
            <div class="mt-2 font-mono text-2xl font-bold text-amber-200">{{ symbol || '-' }}</div>
          </div>

          <div class="rounded-xl border border-amber-300/20 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Data Source</div>
            <div class="mt-2 font-mono text-2xl font-bold text-amber-200">{{ dataSource }}</div>
          </div>

          <div class="rounded-xl border border-slate-700 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">DB Rows</div>
            <div class="mt-2 font-mono text-2xl font-bold text-white">{{ report?.db_rows_used ?? '-' }}</div>
          </div>

          <div class="rounded-xl border border-slate-700 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Report ID</div>
            <div class="mt-2 font-mono text-2xl font-bold text-white">{{ report?.report_id ?? '-' }}</div>
          </div>

          <div class="rounded-xl border border-slate-700 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Report Length</div>
            <div class="mt-2 font-mono text-2xl font-bold text-white">
              {{ hasReport ? `${reportText.length} chars` : '-' }}
            </div>
          </div>

          <div class="rounded-xl border border-slate-700 bg-black/35 p-4 shadow-lg shadow-black/20">
            <div class="text-xs font-medium uppercase tracking-wider text-slate-400">Sync Status</div>
            <div class="mt-2 font-mono text-2xl font-bold" :class="syncResult?.success ? 'text-emerald-200' : 'text-white'">
              {{ syncResult ? (syncResult.success ? 'SUCCESS' : 'FAILED') : '-' }}
            </div>
          </div>
        </section>
      </div>

      <section
        v-if="syncResult"
        class="mt-6 rounded-xl border border-amber-300/20 bg-slate-950/70 p-5 shadow-lg shadow-black/20"
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-sm font-semibold text-white">同步結果</h2>
            <p class="mt-1 text-xs text-slate-400">
              {{ syncResult.start_date ?? startDate }} ~ {{ syncResult.end_date ?? endDate }}
            </p>
          </div>
          <span class="font-mono text-xs text-amber-200/80">
            {{ syncResult.elapsed_seconds ?? '-' }}s
          </span>
        </div>

        <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="[label, value] in syncStats"
            :key="label"
            class="rounded-lg border border-slate-700 bg-black/40 p-3"
          >
            <div class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              {{ label }}
            </div>
            <div class="mt-1 font-mono text-xl font-bold text-amber-200">
              {{ value ?? '-' }}
            </div>
          </div>
        </div>
      </section>

      <section class="mt-6 overflow-hidden rounded-xl border border-amber-300/20 bg-slate-950/80 shadow-lg shadow-black/20">
        <div class="flex items-center justify-between border-b border-amber-300/10 px-5 py-3">
          <h2 class="text-sm font-semibold text-white">Markdown 預覽</h2>
          <span class="font-mono text-xs text-slate-500">{{ hasReport ? 'READY' : 'EMPTY' }}</span>
        </div>

        <pre
          v-if="hasReport"
          class="max-h-[560px] overflow-auto whitespace-pre-wrap break-words p-5 font-mono text-sm leading-7 text-slate-200"
        >{{ reportText }}</pre>

        <div v-else class="p-10 text-center text-sm text-slate-500">
          尚未產生資料包。先同步資料或直接從 DB 產生 Markdown。
        </div>
      </section>

      <div class="mt-6 border-t border-amber-300/10 pt-5 text-center">
        <p class="text-xs text-slate-500">
          JS-Python-Trade-Bridge v1.0 - FastAPI / Vue 3
        </p>
      </div>
    </AppCard>
  </PageShell>
</template>
