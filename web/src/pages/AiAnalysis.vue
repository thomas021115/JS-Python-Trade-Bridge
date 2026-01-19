<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/services/api";
import type { BriefingResponse , AiReportResponse } from "@/services/api";

const symbol = ref("2330");

const briefing = ref<BriefingResponse | null>(null);
const report = ref<AiReportResponse | null>(null);

const loadingBriefing = ref(false);
const loadingReport = ref(false);

const errorMsg = ref<string | null>(null);

console.log("[init]", {
  symbol: symbol.value,
  briefing: briefing.value,
  report: report.value,
});

async function fetchBriefing() {};

async function fetchReport(){
  console.log("[door] fetchReport called");


  try {
    console.log("[before api]");
    const res = await api.getAiReport(symbol.value);
    console.log("[after] res" , res);
  }catch (err){
    console.log("[catch error]", err);
    
  }
  
};



</script>
<template>
  <div style="padding:16px">
    <input v-model="symbol" />
    <button @click="fetchReport">抓</button>
  </div>
</template>