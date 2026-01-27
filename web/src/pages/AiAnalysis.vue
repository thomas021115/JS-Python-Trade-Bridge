<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/services/api";
import type { AiReportResponse } from "@/services/api";
import { downloadMarkdown , buildReportFilename } from "@/utils/download";

const symbol = ref("2330");

const report = ref<AiReportResponse | null>(null);

const loadingReport = ref(false);

const errorMsg = ref<string | null>(null);

console.log("[init]", {
  symbol: symbol.value,
  report: report.value,
});

async function fetchReport(){
  console.log("[door] fetchReport called");

  loadingReport.value = true;
  errorMsg.value = null;

  try {
    console.log("[before api]");
    const res = await api.getAiReport(symbol.value);
    console.log("[after] res" , res);

    if(res.error){
      errorMsg.value = res.error;
      console.log("[res.error]",res.error);
      return;
    }
    report.value = res;
    console.log("[res.error]",res.report?.length);

    const filename = buildReportFilename(res.code);
    downloadMarkdown(filename, res.report ?? "");

  } catch (err) {
    errorMsg.value = "抓取資料失敗 (console / Network)"
    console.log("[catch error]", err);
  }finally {
    loadingReport.value = false;
    console.log("[finally] loadingReport=false");
  }
};


</script>

<template>
  <div style="padding:16px">
    <input v-model="symbol" />
    <button @click="fetchReport" :disabled="loadingReport">抓</button>
  </div>
</template>