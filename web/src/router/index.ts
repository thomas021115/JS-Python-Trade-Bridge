import { createRouter, createWebHistory } from "vue-router";

import AiAnalysis from "@/pages/AiAnalysis.vue"
import Portfolio from "@/pages/Portfolio.vue";
import Todo from "@/pages/Todo.vue"

export const router = createRouter({
history: createWebHistory(),
routes: [
    { path: "/", redirect:"/aianalysis"},
    { path: "/todo", component: Todo},
    { path: "/portfolio", component: Portfolio},
    { path: "/aianalysis", component: AiAnalysis}
],
});