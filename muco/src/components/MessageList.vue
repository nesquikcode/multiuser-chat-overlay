<script setup>
import { computed, nextTick, watch, ref } from 'vue';
import Message from './Message.vue';
import { config, saveConfig } from '@/store/config'

const props = defineProps({
    messages: {
      type: Array,
      required: true
    }
});
let messages = ref(props.messages);
let chatHeight = computed(() => `
  height: calc(${config.data.height}px - ${config.data.themes[config.data.activeTheme].input.height} - 12px);
`)

let messagesRef = ref(null);
watch(
  () => messages.value,
  async () => {
    await nextTick();
    if (messagesRef.value) {
      messagesRef.value.scrollTo({
        top: messagesRef.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  },
  { deep: true }
);

</script>

<template>
  <div class="messages" :style="chatHeight" ref="messagesRef">
    <Message
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
    />
  </div>
</template>

<style>
.messages {
  display: flex;
  flex-direction: column;
  width: 98%;
  overflow-x: hidden;
  overflow-y: auto;
  margin-left: auto;
  margin-right: auto;
}

.messages::-webkit-scrollbar {
  display: none;
}

</style>