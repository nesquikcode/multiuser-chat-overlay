<script setup>
import { ref, computed, version } from 'vue';
import MessageList from './MessageList.vue';
import MessageInput from './MessageInput.vue';
import { wsService } from '@/services/ws';
import { config, saveConfig, reloadConfig } from '@/store/config';
import { ipc } from '@/services/ipc';

let currentTheme = ref(config.data.themes[config.data.activeTheme]);
let messages = ref([]);

let connip = null;
let connport = null;

function addMessage(text, author = config.data.nickname, id = Date.now()) {
  messages.value.push({
    id: id,
    text,
    author: author
  })
};

function sendMessage(text) {
  if (wsService.socket && !text.startsWith("!")) {
    wsService.send({
      type: "message",
      author: config.data.nickname,
      text: text,
      id: Date.now()
    });
  } else {
    if (!text.startsWith("!")) {addMessage(text, config.data.nickname, Date.now());return}
    let cmd = text.replace("!", "").split(" ");
    if (cmd[0] == "help") {
      addMessage("[описание]", "[команда]");
      addMessage("Список команд", "help");
      addMessage("Поменять ник: nick [nick]", "nick");
      addMessage("Очистить чат", "clean");
      addMessage("Перезагрузить чат", "reload");
      addMessage("Список серверов", "list");
      addMessage("Добавить сервер в список серверов: add ws(s)://[ip(:port)]", "add");
      addMessage("Удалить сервер из списка серверов: del [index]", "del");
      addMessage("Подключиться к серверу: con ws(s)://[ip(:port)]", "con");
      addMessage("Подключиться к серверу из списка: conl [index]", "conl");
      addMessage("Отключиться от сервера", "dcon");
      addMessage("Открыть конфиг MUCO", "config");
      addMessage("Перезапустить MUCO", "restart");
      addMessage("Выйти из MUCO", "exit");
    } else
    if (cmd[0] == "clean") {
      messages.value.splice(0, messages.value.length);
    } else
    if (cmd[0] == "reload") {
      wsService.send({
        type: "getHistory"
      })
    } else
    if (cmd[0] == "con") {
      addMessage(`Подключение к ${cmd[1]}...`, "system")
      wsService.connect(cmd[1]);
    } else
    if (cmd[0] == "nick") {
      let nick = cmd[1];
      config.data.nickname = nick;
      saveConfig();
      addMessage(`Ник изменен на '${nick}'.`, "system");
    } else
    if (cmd[0] == "add") {
      let server = cmd[1];
      config.data.servers.push(server);
      saveConfig();
      addMessage(`Добавлен сервер ${server}.`, "system");
    } else
    if (cmd[0] == "del") {
      let serverIndex = cmd[1];
      let server = config.data.servers[serverIndex];
      config.data.servers.splice(serverIndex, 1);
      saveConfig();
      addMessage(`Удален сервер ${server}.`, "system");
    } else
    if (cmd[0] == "conl") {
      let server = config.data.servers.at(Number(cmd[1]));
      if (server) {
        addMessage(`Подключение к ${server}...`, "system")
        wsService.connect(server);
      } else {
        addMessage("Такого индекса нет в списке.", "system");
      }
    } else
    if (cmd[0] == "dcon") {
      wsService.send({type: "disconnect"});
    } else
    if (cmd[0] == "restart") {
      ipc.restartApp();
    } else
    if (cmd[0] == "config") {
      ipc.openConfigFolder();
    } else
    if (cmd[0] == "exit") {
      if (wsService.socket) {wsService.send({type: "disconnect"});}
      window.close();
    } else
    if (cmd[0] == "list") {
      addMessage("Список серверов:", "system");
      let i = 0;
      for (let server of config.data.servers) {
        addMessage(`#${i} - ${server}`, "system");
        i++;
      }
      if (config.data.servers.length == 0) {
        addMessage(" - нет серверов - ", "system");
      }
    }
    else {
      addMessage(text, config.data.nickname, Date.now());
    }
  }
}

function processWsData(data) {
  console.log(data);
  let content = data;
  if (content.type == "connaccept") {
    addMessage(`Подключено к ${content.ip}:${content.port}.`);
    wsService.send({type: "getHistory"});
    connip = content.ip;
    connport = content.port;
  } else if (content.type == "connreject") {
    addMessage(`Ошибка подключения к ${content.ip}:${content.port}.`);
    addMessage(` - ${content.error}`);
  } else if (content.type == "connclose") {
    addMessage(`Сервер ${connip}:${connport} закрыл подключение.`);
    connip = null;
    connport = null;
  } else if (content.type == "history") {
    messages.value.splice(0, messages.value.length);
    addMessage("Чат очищен. Загружается история чата сервера...", "system");
    for (let msg of content.messages) {
      addMessage(msg.text, msg.author, msg.id);
    };
  } else if (content.type == "message") {
    addMessage(content.text, content.author, content.id);
  } else if (content.type == "dcon-agree") {
    addMessage("Отключено от сервера.", "system", Date.now());
  }
}

let chatTheme = computed(() => `
  background: ${currentTheme.value.base.basecolor};
  color: ${currentTheme.value.base.textcolor};
  font-family: ${currentTheme.value.base.font};
  font-size: ${currentTheme.value.base.fontsize};
  font-weight: ${currentTheme.value.base.fontboldness};
`);

addMessage(`MUCO на Vue ${version}.`, "system");
wsService.subscribe(processWsData);
if (config.data.servers.length > 0 && config.data.autoConnectTo != -1) {
  wsService.connect(`ws://${config.data.servers[config.data.autoConnectTo]}`);
} else {
  addMessage("Чат не подключен к серверу.", "setup");
  addMessage("Для подключения нужно настроить muco.json:", "setup");
  addMessage(" 1 - указать ник в nickname", "setup");
  addMessage(" 2 - добавить URL сервера в servers", "setup");
  addMessage(" 3 - указать индекс URL сервера в autoConnectTo", "setup");
  addMessage("или", "");
  addMessage(" 1 - добавить сервер в список используя add", "setup");
  addMessage(" 2 - подключиться используя conl 0", "setup");
  addMessage("-=-=-=-=-=-=-=-=-", "");
  addMessage("Активные бинды:", "system");
  addMessage(" Enter - отправить сообщение", "system");
  addMessage(` ${config.data.typeKeybinds.join(' ')} - переключить фокус чата`, "system");
  addMessage("Доп. команды: !help", "system");
}
</script>

<template>
  <div class="chat" :style="chatTheme">
    <MessageList :messages="messages" />
    <MessageInput @send="sendMessage" />
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
