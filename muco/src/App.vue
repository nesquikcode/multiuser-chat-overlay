

<script setup>
import { ref, computed, onMounted } from 'vue';
import Chat from './components/Chat.vue';
import { config, saveConfig } from '@/store/config'
import { loadFonts } from './config/font';
let theme = ref(config.data.themes[config.data.activeTheme]);
let computedStyle = computed(() =>`
--background: ${theme.value.base.basecolor};
--color: ${theme.value.base.textcolor};
--font: ${theme.value.base.font};
--fontsize: ${theme.value.base.fontsize};
--boldness: ${theme.value.base.fontboldness};
`);

document.documentElement.style.setProperty("--background", theme.value.base.basecolor);
document.documentElement.style.setProperty("--color", theme.value.base.textcolor);
document.documentElement.style.setProperty("--font", theme.value.base.font);
document.documentElement.style.setProperty("--fontsize", theme.value.base.fontsize);
document.documentElement.style.setProperty("--bolddness", theme.value.base.fontboldness);

onMounted(() => {
  loadFonts();
})

</script>

<style>
:root {
  overflow: hidden;
}
#app {
  display: flex;
  position: relative;
  width: 100dvw;
  height: 100dvh;
}
</style>

<template>
  <Chat v-if="config.ready" :style="computedStyle"/>
</template>