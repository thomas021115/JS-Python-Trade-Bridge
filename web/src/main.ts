import { createApp } from "vue";
import App from "./App.vue";
import { router } from "./router";
import "./style.css";
import Vue3Toastify from "vue3-toastify";
import "vue3-toastify/dist/index.css" //node_modules裡的vue3-toastify

createApp(App).use(router).use(Vue3Toastify, {position: "top-right",autoClose: 2000,}).mount("#app"); //引入並預設Vue3Toastify 位置
