<template>
	<div id="app">
		<!-- 導覽列 -->
		<nav class="navbar">
			<div class="nav-brand">JS-Python Trade Bridge</div>
			<div class="nav-links">
				<router-link to="/">AI 分析</router-link>
				<router-link to="/portfolio">投資組合</router-link>
				<router-link to="/todo">練習板</router-link>
			</div>
		</nav>

		<!-- 頁面呈現區域 -->
		<main class="container">
			<router-view></router-view>
		</main>
	</div>
</template>

<style scoped>
.navbar {
	display: flex;
	justify-content: space-between;
	padding: 1rem 2rem;
	background-color: #2c3e50;
	color: white;
}
.nav-links a {
	color: white;
	margin-left: 1.5rem;
	text-decoration: none;
}
.nav-links a.router-link-active {
	font-weight: bold;
	color: #42b983;
}
.container {
	padding: 2rem;
}
</style>
