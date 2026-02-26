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
	<div class="p-6 max-w-md mx-auto space-y-4">
		<h1 class="text-xl font-bold">Todo</h1>
		<div class="flex gap-2">
			<input v-model="input"
			@keydown.enter="addTodo"
			placeholder="輸入代辦事項"
			class="flex-1 rounded border px-3 py-2"
			/>
			<button
			@click="addTodo"
			class="px-4 py-2 rounded bg-slate-900 text-white"
			>
			新增
		</button>
		</div>

		<ul class="space-y-2">
			<li v-for="todo in todos"
			:key="todo.id"
			class="flex item-center justify-between rounded border px-3 py-2"
			>
			<span>{{ todo.text }}</span>
			<button @click="removeTodo(todo.id)"
			class="text-sm text-red-500"
			>
			刪除
			</button>
		</li>
		</ul>
	</div>
</template>
