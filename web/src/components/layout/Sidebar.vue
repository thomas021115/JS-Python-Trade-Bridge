<script setup lang="ts">
import Logo from "@/assets/icon/Logo.svg";
import {
	House,
	LayoutDashboard,
	Presentation,
	Newspaper,
	BookMarked,
} from "lucide-vue-next";
</script>

<template>
	<aside class="flex flex-col h-screen w-56 bg-white text-black">
		<div class="flex h-28 justify-center items-center">
			<img :src="Logo" alt="logo-icon" class="w-8 h-8 mr-3" /><span
				class="text-xl font-semibold"
				>TradeBridge</span
			>
		</div>
		<nav class="flex flex-1 px-8">
			<ul class="menu-list space-y-3 w-full">
				<li>
					<router-link to="/">
						<House class="w-5 h-5" />
						<span>首頁</span>
					</router-link>
				</li>
				<li>
					<router-link to="/Dashboard">
						<LayoutDashboard class="w-5 h-5" />
						<span>儀表板</span>
					</router-link>
				</li>
				<li>
					<router-link to="/AiAnalysis"
						><Presentation class="w-5 h-5" />
						<span>AI 分析</span>
					</router-link>
				</li>
				<li>
					<router-link to="/News"
						><Newspaper class="w-5 h-5" />
						<span>新聞快報</span>
					</router-link>
				</li>
				<li>
					<router-link to="/Watchlist"
						><BookMarked class="w-5 h-5" />
						<span>自選清單</span>
					</router-link>
				</li>
			</ul>
		</nav>
	</aside>
</template>

<style scoped>
@reference "../../style.css";

.menu-list a {
	@apply flex items-center gap-4  px-4 py-2 rounded-xl hover:bg-slate-100;
}
.menu-list a.router-link-active {
	@apply bg-slate-200;
}
</style>
