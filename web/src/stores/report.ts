import { defineStore } from 'pinia';
import { api } from '@/services/api';
import { downloadMarkdown, buildReportFilename } from '@/utils/download';
import { toast } from 'vue3-toastify';
import type { AiReportResponse, SyncResponse } from '@/services/api';

function formatDate(date: Date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function defaultStartDate() {
  const date = new Date();
  date.setDate(date.getDate() - 7);
  return formatDate(date);
}

export const useReport = defineStore('report', {
  state: () => ({
    symbol: '2330',
    startDate: defaultStartDate(),
    endDate: formatDate(new Date()),
    report: null as AiReportResponse | null,
    loadingReport: false,
    errorMsg: null as string | null,
    syncing: false,
    syncResult: null as SyncResponse | null,
    syncErrorMsg: null as string | null,
  }),
  actions: {
    async fetchreport() {
      this.loadingReport = true;
      this.errorMsg = null;

      try {
        const res = await api.getAiReport(this.symbol, this.startDate, this.endDate);
        this.report = res;

        if (res.error && !res.report) {
          this.errorMsg = res.message ?? res.error;
          toast.error(this.errorMsg);
          return;
        }

        if (res.data_quality_warning) {
          toast.warning(res.message ?? '資料不足，請先同步資料');
        }

        if (res.report) {
          const filename = buildReportFilename(res.code);
          downloadMarkdown(filename, res.report);
          toast.success('資料包已產生並下載');
          return;
        }

        this.errorMsg = res.message ?? res.error ?? '後端沒有回傳 Markdown 內容';
        toast.error(this.errorMsg);
      } catch (err) {
        this.errorMsg = '產生資料包失敗，請確認後端服務或網路狀態';
        toast.error(this.errorMsg);
        console.log('[store.report fetchreport catch]', err);
      } finally {
        this.loadingReport = false;
      }
    },
    async syncData() {
      this.syncing = true;
      this.syncErrorMsg = null;
      this.syncResult = null;

      try {
        const res = await api.syncStockData(this.symbol, this.startDate, this.endDate);
        this.syncResult = res;

        if (!res.success) {
          this.syncErrorMsg = res.message ?? res.error ?? '同步資料失敗';
          toast.error(this.syncErrorMsg);
          return;
        }

        toast.success('資料同步完成');
      } catch (err) {
        this.syncErrorMsg = '同步資料失敗，請確認 Shioaji 連線或後端服務';
        toast.error(this.syncErrorMsg);
        console.log('[store.report syncData catch]', err);
      } finally {
        this.syncing = false;
      }
    },
  },
});
