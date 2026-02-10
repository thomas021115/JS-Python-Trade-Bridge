<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Search } from 'lucide-vue-next';

const stockCode = ref('');
const router = useRouter();

const handleSearch = () => {
	if (!stockCode.value.trim()) return;

	router.push({
		path: '/aianalysis',
		query: {
			stockCode: stockCode.value,
		},
	});
	stockCode.value = '';
};
</script>

<template>
	<header
		class="flex bg-white ml-0.5 border-slate-200 h-16 items-center justify-between px-6 sticky top-0 z-20"
	>
		<div class="flex items-center ml-10">
			<div class="relative w-64">
				<span class="absolute inset-y-0 left-2 flex items-center"
					><Search class="w-4 h-4 text-slate-400"
				/></span>
				<input
					type="text"
					v-model="stockCode"
					@keydown.enter="handleSearch"
					class="block w-full border border-slate-300 rounded-xl pl-8 py-2 text-sm"
					placeholder="搜尋代碼/名稱"
				/>
			</div>
		</div>

		<div class="flex items-center gap-4">Right Zone</div>
	</header>
</template>
