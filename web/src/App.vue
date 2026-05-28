<template>
  <div id="app" class="app-shell">
    <nav class="navbar">
      <div class="nav-brand">JS-Python Trade Bridge</div>
      <div class="nav-links">
        <router-link to="/">AI 分析</router-link>
        <router-link to="/portfolio">投資組合</router-link>
        <router-link to="/todo">練習板</router-link>
      </div>
    </nav>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 12% 0%, rgba(212, 175, 55, 0.14), transparent 32%),
    linear-gradient(135deg, #020617 0%, #030712 42%, #050816 100%);
  color: #e5e7eb;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1rem 2rem;
  background: rgba(2, 6, 23, 0.88);
  border-bottom: 1px solid rgba(212, 175, 55, 0.22);
  color: #f8fafc;
  backdrop-filter: blur(14px);
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
}

.nav-brand {
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #f8fafc;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.nav-links a {
  color: #cbd5e1;
  text-decoration: none;
  font-size: 0.92rem;
  transition:
    color 160ms ease,
    text-shadow 160ms ease;
}

.nav-links a:hover {
  color: #f5d56e;
  text-shadow: 0 0 18px rgba(245, 213, 110, 0.28);
}

.nav-links a.router-link-active {
  font-weight: 700;
  color: #f5d56e;
}

.container {
  width: 100%;
  max-width: 1900px;
  min-height: calc(100vh - 57px);
  margin: 0 auto;
  padding: 0;
  background: transparent;
}

@media (max-width: 640px) {
  .navbar {
    align-items: flex-start;
    flex-direction: column;
    padding: 1rem;
  }

  .nav-links {
    gap: 0.9rem;
  }
}
</style>
