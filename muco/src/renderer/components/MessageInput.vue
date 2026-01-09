<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick, defineEmits } from 'vue';
import { config } from '@/renderer/store/config'

let theme = computed(() => config.data.themes[config.data.activeTheme]);
let inputTheme = computed(() => `
  width: ${theme.value.input.width};
  height: ${theme.value.input.height};
  --placeholder: ${theme.value.input.color};
`);
let placeholder = computed(() => {return theme.value.input.placeholdertext});

const emit = defineEmits(['send']);

let text = ref("");
let msgHistory = ref([""]);
let historyIndex = ref(-1);
let messages = ref([]);
const inputRef = ref(null);

function sendMessage() {
  if (!text.value.trim()) return;

  emit('send', text.value);

  if (text.value != "") {msgHistory.value.push(text.value);historyIndex.value = msgHistory.value.length-1;}
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

function upHistory() {
  if (text.value != "") {historyIndex.value--;}
  if (historyIndex.value < 0) {
    historyIndex.value = 0;
    text.value = msgHistory.value[historyIndex.value];
  } else {
    text.value = msgHistory.value[historyIndex.value];
  }
}

function downHistory() {
  historyIndex.value++;
  if (historyIndex.value+1 > msgHistory.value.length) {
    historyIndex.value--;
  } else {
    text.value = msgHistory.value[historyIndex.value];
  }
}

onMounted(() => {
  globalThis.addEventListener('type-event', onTypeEvent);
  globalThis.addEventListener('stop-type-event', onStopTypeEvent);
});

onUnmounted(() => {
  globalThis.removeEventListener('type-event', onTypeEvent);
  globalThis.removeEventListener('stop-type-event', onStopTypeEvent);
});

</script>

<template>
  <textarea
    ref="inputRef"
    v-model="text"
    :style="inputTheme"
    class="message-input"
    id="input"
    :placeholder="placeholder"
    @keydown.enter.prevent="sendMessage"
    @keydown.up.prevent="upHistory"
    @keydown.down.prevent="downHistory"
    ></textarea>
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