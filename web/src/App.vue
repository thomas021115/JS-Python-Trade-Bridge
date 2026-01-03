<template>
  <div style="padding: 16px">
   <nav style="display:flex; gap: 12px; margin-bottom: 10px;">
    <RouterLink to="/todo">Todo</RouterLink>
    <RouterLink to="/portfolio">Portfolio</RouterLink>
    <RouterLink to="/aianalysis">AiAnalysis</RouterLink>
   </nav>
   <RouterView />
  </div>

</template>

