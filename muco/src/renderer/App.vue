<script setup>
import { computed, onMounted } from 'vue';
import Chat from '@/renderer/components/chat/Chat.vue';
import { config } from '@/renderer/store/config'
import { loadFonts } from '@/renderer/config/font';
let settingExpanded = ref(false);
let theme = computed(() => config.data.themes[config.data.activeTheme]);
let computedStyle = computed(() =>`
--background: ${theme.value.base.basecolor};
--color: ${theme.value.base.textcolor};
--font: ${theme.value.base.font};
--fontsize: ${theme.value.base.fontsize};
--boldness: ${theme.value.base.fontboldness};
`);

onMounted(() => {
  loadFonts();
})

</script>

<style>
a {
  color: inherit;
  transition: all 0.15s ease;
}
*:focus {
  outline: none !important;
}
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
  <Chat
    v-if="config.ready && !settingExpanded.value"
    :style="computedStyle"
    :settingExpanded="settingExpanded"
    @set-setting-expanded="settingExpanded.value = $event"
  />
</template>