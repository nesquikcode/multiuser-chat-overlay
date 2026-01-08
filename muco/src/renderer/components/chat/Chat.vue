<script setup>
import { ref, computed, onMounted } from 'vue';
import MessageList from '@/renderer/components/MessageList.vue';
import MessageInput from '@/renderer/components/MessageInput.vue';
import { wsService } from '@/renderer/services/ws';
import { config } from '@/renderer/store/config';
import { ipc } from '@/renderer/services/ipc';
import { MUCOReceiver, MUCOSender, MUCOData } from '@/renderer/services/api';
import { Chat } from '@/renderer/components/chat/chat';
import { checkUpdates, fileToBase64, removePrefix } from '@/renderer/utils/utils';

let data = new MUCOData(wsService, config)

let receiver = new MUCOReceiver(data);
let sender = new MUCOSender(data);

let messages = ref([]);
let chat = new Chat(sender, config, wsService, messages);
data.chat = chat;

let currentTheme = computed(() => config.data.themes[config.data.activeTheme]);
let chatTheme = computed(() => `
  background: ${currentTheme.value.base.basecolor};
  color: ${currentTheme.value.base.textcolor};
  font-family: ${currentTheme.value.base.font};
  font-size: ${currentTheme.value.base.fontsize};
  font-weight: ${currentTheme.value.base.fontboldness};
`);

window.addEventListener('drop', async (e) => {
  e.preventDefault();
  const files = Array.from(e.dataTransfer.files);
  if (files.length > 1) {console.log("Got more than 1 file in drag&drop. Ignoring unexcepted.")}
  
  let file = files[0];

  const data = await fileToBase64(file);
  if (file.type.startsWith('image/')) {
    chat.sendMessage(`<img src="${data}"></img>`);
  } else if (file.type.startsWith('video/')) {
    chat.sendMessage(`<video controls src="${data}"></video>`);
  } else if (file.type.startsWith('audio/')) {
    chat.sendMessage(`<audio controls src="${data}"></audio>`);
  } else {
    chat.addMessage("Неизвестный тип файла.", "system");
  }
});

window.addEventListener('add-message', async (e, msg, from) => {
  chat.addMessage(msg, from);
})

onMounted(async () => {
  let mucover = await ipc.getVersion();
  chat.addMessage(`MUCO ${mucover}`, "system");
  if (config.data.servers.length > 0 && config.data.autoConnectTo != -1) {
    sender.connect(config.data.servers[config.data.autoConnectTo]);
  } else {
    chat.addMessage("Чат не подключен к серверу.", "setup");
    chat.addMessage("Для настройки MUCO стоит прочитать <a href='https://github.com/nesquikcode/multiuser-chat-overlay/wiki/%D0%9A%D0%BE%D0%BD%D1%84%D0%B8%D0%B3-muco.json' target='_blank'>wiki по конфигу</a>.", "setup")
    chat.addMessage("Активные бинды:", "system");
    chat.addMessage("  Enter - отправить сообщение", "system");
    chat.addMessage(`  ${config.data.typeKeybinds.join(' ')} - переключить фокус чата`, "system");
    chat.addMessage(`Доп. команды: ${config.data.commandPrefix}help`, "system");
  }
  checkUpdates(chat);
})
</script>

<template>
  <div class="chat" :style="chatTheme">
    <MessageList :messages="messages" />
    <MessageInput @send="(text) => chat.sendMessage(text)" />
  </div>
</template>

<style>
.chat {
  display: flex;
  height: 100%;
  width: 100%;
  -webkit-app-region: drag;
  overflow: hidden;
}
</style>
