<script setup lang="ts">
import { computed, watch } from "vue";
import { storeToRefs } from "pinia";
import PageShell from "@/components/layout/PageShell.vue";
import AppCard from "@/components/ui/AppCard.vue";
import { useReport } from "@/stores/report";

const s = useReport();
const { symbol, report, loadingReport, errorMsg } = storeToRefs(s);

const reportText = computed(() => report.value?.report?.trim() ?? "");
const hasReport = computed(() => reportText.value.length > 0);
const statusLabel = computed(() => {
  if (loadingReport.value) return "產生中";
  if (errorMsg.value) return "發生錯誤";
  if (hasReport.value) return "已完成";
  return "待命";
});

watch(symbol, () => {
  errorMsg.value = null;
  report.value = null;
});

function fetchReport() {
  const code = symbol.value.trim();

  if (!code) {
    errorMsg.value = "請先輸入股票代號。";
    return;
  }

  if (!/^\d{4,6}$/.test(code)) {
    errorMsg.value = "股票代號格式看起來不正確，請輸入 4 到 6 位數字。";
    return;
  }

  symbol.value = code;
  return s.fetchreport();
}
</script>

<template>
  <PageShell variant="center">
    <AppCard>
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-slate-900">
            AI 技術分析
          </h1>
          <p class="mt-2 text-sm leading-relaxed text-slate-500">
            輸入台股代號，呼叫 Python 後端產生技術分析報告。<br />
            產生完成後會自動下載 Markdown，並在下方顯示預覽。
          </p>
        </div>

        <span
          class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors duration-300"
          :class="
            loadingReport
              ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/20'
              : errorMsg
                ? 'bg-red-50 text-red-700 ring-1 ring-red-600/20'
                : 'bg-slate-100 text-slate-600 ring-1 ring-slate-500/10'
          "
        >
          <span class="relative flex h-2 w-2">
            <span
              v-if="loadingReport"
              class="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"
            />
            <span
              class="relative inline-flex h-2 w-2 rounded-full"
              :class="loadingReport ? 'bg-blue-500' : errorMsg ? 'bg-red-500' : 'bg-slate-400'"
            />
          </span>
          {{ statusLabel }}
        </span>
      </div>

      <div class="mt-8 space-y-6">
        <div class="space-y-4">
          <label class="block text-sm font-medium text-slate-700">股票代號</label>

          <div class="flex gap-3">
            <div class="group relative flex-1">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <span class="font-mono text-sm text-slate-400">TW.</span>
              </div>
              <input
                v-model.trim="symbol"
                type="text"
                inputmode="numeric"
                placeholder="2330"
                :disabled="loadingReport"
                @keydown.enter="!loadingReport ? fetchReport() : null"
                class="block w-full rounded-xl border-0 py-3 pl-12 pr-4 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 transition-shadow duration-200 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 disabled:bg-slate-50 disabled:text-slate-500 sm:text-sm sm:leading-6"
              />
            </div>

            <button
              type="button"
              :disabled="loadingReport"
              class="inline-flex shrink-0 items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-900 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              @click="fetchReport"
            >
              <svg
                v-if="loadingReport"
                class="-ml-1 h-4 w-4 animate-spin text-white"
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
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <svg
                v-else
                class="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              {{ loadingReport ? "產生中..." : "產生報告" }}
            </button>
          </div>
        </div>

        <div v-if="errorMsg" class="flex gap-3 rounded-lg border border-red-100 bg-red-50 p-4">
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
            <h3 class="font-medium">無法產生報告</h3>
            <p class="mt-1 opacity-90">{{ errorMsg }}</p>
          </div>
        </div>

        <div class="rounded-xl bg-slate-50/50 p-5 ring-1 ring-slate-200">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-900">執行狀態</h3>
            <span class="font-mono text-xs text-slate-500">
              {{ hasReport ? "SUCCESS" : "IDLE" }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100">
              <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
                Target
              </div>
              <div class="mt-1 font-mono text-lg font-bold text-slate-900">
                {{ symbol || "-" }}
              </div>
            </div>
            <div class="rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100">
              <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
                Report Length
              </div>
              <div class="mt-1 font-mono text-lg font-bold text-slate-900">
                {{ hasReport ? `${reportText.length} chars` : "-" }}
              </div>
            </div>
            <div class="rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100">
              <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
                Daily Saved
              </div>
              <div class="mt-1 font-mono text-lg font-bold text-slate-900">
                {{ report?.daily_price_saved ?? "-" }}
              </div>
            </div>
            <div class="rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100">
              <div class="text-xs font-medium uppercase tracking-wider text-slate-500">
                Report ID
              </div>
              <div class="mt-1 font-mono text-lg font-bold text-slate-900">
                {{ report?.report_id ?? "-" }}
              </div>
            </div>
          </div>
        </div>

        <div class="overflow-hidden rounded-xl bg-white ring-1 ring-slate-200">
          <div class="border-b border-slate-100 px-5 py-3">
            <h3 class="text-sm font-semibold text-slate-900">報告預覽</h3>
          </div>

          <pre
            v-if="hasReport"
            class="max-h-[520px] overflow-auto whitespace-pre-wrap break-words p-5 text-sm leading-7 text-slate-700"
          >{{ reportText }}</pre>

          <div v-else class="p-8 text-center text-sm text-slate-500">
            尚未產生報告。輸入股票代號後按下「產生報告」開始。
          </div>
        </div>
      </div>

      <div class="mt-6 border-t border-slate-100 pt-6 text-center">
        <p class="text-xs text-slate-400">
          JS-Python-Trade-Bridge v1.0 - Powered by FastAPI & Vue 3
        </p>
      </div>
    </AppCard>
  </PageShell>
</template>
