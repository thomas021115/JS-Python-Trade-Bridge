<script setup lang="ts">
import { ref } from 'vue';
import { api } from '@/services/api'; // 引入我們寫好的 api
import type { BriefingResponse } from '@/services/api'; // 引入型別

const symbol = ref('2330');
const aiData = ref<BriefingResponse | null>(null);
const loading = ref(false);

async function fetchAnalysis() {
  loading.value = true;
  try {
  
    const res = await api.getAiBriefing(symbol.value);
    
    if (res.error) {
      alert(res.error);
      return;
    }

    aiData.value = res;

    console.log('取得資料:', res.rows[0]?.close); 
  } catch (err) {

    console.error('請求失敗', err);
  } finally {

    loading.value = false;

  }
}
</script>

<template>
  <div>
    <input v-model="symbol" />
    <button @click="fetchAnalysis">分析</button>
    
    <div v-if="aiData">
      <p>股票代碼: {{ aiData.code }}</p>
      </div>
  </div>
</template>