<script setup lang="ts">
import { Search } from 'lucide-vue-next';
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
					class="block w-full border border-slate-300 rounded-xl pl-8 py-2 text-sm"
					placeholder="搜尋代碼/名稱"
				/>
			</div>
		</div>

		<div class="flex items-center gap-4">Right Zone</div>
	</header>
</template>
