<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick, defineEmits } from 'vue';
import { config, saveConfig } from '@/store/config'

let theme = ref(config.data.themes[config.data.activeTheme]);
let inputTheme = computed(() => `
  width: ${theme.value.input.width};
  height: ${theme.value.input.height};
  --placeholder: ${theme.value.input.placeholdercolor};
`);

const emit = defineEmits(['send']);

let text = ref("");
let messages = ref([]);
const inputRef = ref(null);

function sendMessage() {
  if (!text.value.trim()) return;

  emit('send', text.value);

  text.value = "";
};

function onTypeEvent() {
  console.log("focusing");
  nextTick(() => {
    inputRef.value?.focus();
  });
};

function onStopTypeEvent() {
  console.log("unfocusing");
  document.activeElement?.blur();
};

onMounted(() => {
  window.addEventListener('type-event', onTypeEvent);
  window.addEventListener('stop-type-event', onStopTypeEvent);
});

onUnmounted(() => {
  window.removeEventListener('type-event', onTypeEvent);
  window.removeEventListener('stop-type-event', onStopTypeEvent);
});

</script>

<template>
  <textarea ref="inputRef" v-model="text" :style="inputTheme" class="message-input" id="input" placeholder="Type a message..." @keydown.enter.prevent="sendMessage"></textarea>
</template>

<style scoped>
.message-input {
  -webkit-app-region: no-drag;
  display: flex;
  position: fixed;
  bottom: 0;
  resize: none;
  border: none;
  background: var(--background);
  color: var(--color);
  outline: none;
}

.message-input::placeholder {
  color: var(--placeholder);
}

</style>