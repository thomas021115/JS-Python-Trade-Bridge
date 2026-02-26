import { defineStore } from 'pinia';
import { api } from "@/services/api";
import { downloadMarkdown , buildReportFilename } from "@/utils/download";
import { toast } from "vue3-toastify";
import type { AiReportResponse } from "@/services/api";

//https://pinia.vuejs.org/zh/core-concepts/
//因為沒有computed/watch組合所以先用option store
export const useReport = defineStore("report", 
    {
        state:() => ({
            symbol:"2330",
            report: null as AiReportResponse | null,
            loadingReport: false,
            errorMsg: null as string | null,
        }),
        actions: {
            async fetchreport(){
                this.loadingReport = true;
                this.errorMsg = null;
                
                try {
                    const res = await api.getAiReport(this.symbol);

                    if (res.error){
                        this.errorMsg = res.error;
                        toast.error(this.errorMsg);
                        return;
                                  }
                    this.report = res;

                    const filename = buildReportFilename(res.code);
                    downloadMarkdown(filename, res.report ?? "");
                    toast.success("下載完成");
                    } catch (err) {
                            this.errorMsg = "抓取資料失敗 (console / Network)";
                            toast.error(this.errorMsg);
                            console.log("[store.download catch]", err);
                    } finally {
                        this.loadingReport = false;
                    }
            },
        },
    });