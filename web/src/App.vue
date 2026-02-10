<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue';
</script>

<template>
	<div class="flex h-screen bg-slate-50 overflow-hidden">
		<Sidebar class="flex-shrink-0" />

		<div class="flex-1 flex flex-col min-w-0">
			<main class="flex-1 overflow-auto p-6">
				<router-view></router-view>
			</main>
		</div>
	</div>
</template>

<style></style>
