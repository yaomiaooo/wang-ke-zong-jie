<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
:root {
  --color-primary: #c4b5e0;
  --color-primary-dark: #5c4d82;
  --color-secondary: #e8e8e8;
  --color-accent-mint: #b8cbb8;
  --color-accent-pink: #dfb5b5;
  --color-accent-orange: #e8c49b;
  --color-accent-purple: #c4b5e0;
  --color-text-primary: #2d2d2d;
  --color-text-secondary: #5c5c5c;
  --color-text-muted: #8a8a8a;
  --color-background: #c4b5e0;
  --color-surface: #ffffff;
  --radius-lg: 1.5rem;
  --radius-md: 1rem;
  --radius-sm: 0.5rem;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.15);
}

body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

#app {
  min-height: 100vh;
}

* {
  box-sizing: border-box;
}
</style>
