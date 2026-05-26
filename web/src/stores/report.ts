import { defineStore } from "pinia";
import { api } from "@/services/api";
import { downloadMarkdown, buildReportFilename } from "@/utils/download";
import { toast } from "vue3-toastify";
import type { AiReportResponse } from "@/services/api";

function formatDate(date: Date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

function defaultStartDate() {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return formatDate(date);
}

export const useReport = defineStore("report", {
    state: () => ({
        symbol: "2330",
        startDate: defaultStartDate(),
        endDate: formatDate(new Date()),
        report: null as AiReportResponse | null,
        loadingReport: false,
        errorMsg: null as string | null,
    }),
    actions: {
        async fetchreport() {
            this.loadingReport = true;
            this.errorMsg = null;

            try {
                const res = await api.getAiReport(this.symbol, this.startDate, this.endDate);

                if (res.error) {
                    this.errorMsg = res.error;
                    toast.error(this.errorMsg);
                    return;
                }

                this.report = res;

                const filename = buildReportFilename(res.code);
                downloadMarkdown(filename, res.report ?? "");
                toast.success("報告已產生");
            } catch (err) {
                this.errorMsg = "無法取得報告，請檢查後端或 Network。";
                toast.error(this.errorMsg);
                console.log("[store.report catch]", err);
            } finally {
                this.loadingReport = false;
            }
        },
    },
});
