<script setup lang="ts">
import { ref } from "vue";
	type TodoItem = {
		id: number;
		text: string;
	};

const input = ref("");
const todos = ref<TodoItem[]>([]);

function addTodo(){

	const newTodo = {
		id: Date.now(),
		text: input.value,
	};
	const newTodos = [];
	for (const t of todos.value){
		newTodos.push(t);
	}
	newTodos.push(newTodo);

	todos.value = newTodos;
	input.value = "";
}

function removeTodo(id: number){
	const newTodos = [];

	for (const t of todos.value){
		if(t.id !== id){
			newTodos.push(t);
		}
	}
	todos.value = newTodos;
}

</script>

<template>
	<div>
		<button @click="count = count + 1">{{ count }}</button>
		<h1>開發筆記 / Todo</h1>
		<p>用於練習 Vue 組件化與 Pinia 狀態管理 [3]。</p>
	</div>
</template>
