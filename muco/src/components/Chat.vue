<script setup>
import { ref, computed, version, onMounted } from 'vue';
import MessageList from './MessageList.vue';
import MessageInput from './MessageInput.vue';
import { wsService } from '@/services/ws';
import { config, saveConfig, reloadConfig } from '@/store/config';
import { ipc } from '@/services/ipc';
import { MUCOAPI } from '@/services/api';

let api = new MUCOAPI(wsService);
let currentTheme = ref(config.data.themes[config.data.activeTheme]);
let messages = ref([]);
let connectedServer = "";
let connected = false;
let checker = null;

function checkOnline() {
  if (connected & (wsService.socket == null)) {
    addMessage("Отключено от сервера.", "system");
    connected = false;

    if (config.data.autoReconnect) {
      addMessage("Переподключение к серверу...", "system");
      wsService.connect(connectedServer);
    } else {
      connectedServer = "";
    }
  }
}

function addMessage(text, author = config.data.nickname, id = Date.now()) {
  messages.value.push({
    id: id,
    text,
    author: author
  })
};

function sendMessage(text) {
  if (text == null) {return;}
  if (config.data.blurOnEnter) {ipc.blurWindow();}
  if (wsService.socket && !text.startsWith("!")) {
    api.sendMessage(config.data.nickname, text);
  } else {
    if (!text.startsWith("!")) {addMessage(text, config.data.nickname);return}
    let cmd = text.replace("!", "").split(" ");
    if (cmd[0] == "help") {
      addMessage("[описание]", "[команда]");
      addMessage("Список команд", "help");
      addMessage("Добавить текст в пресеты: padd [key] [text]", "padd");
      addMessage("Удалить текст из пресетов: pdel [key]", "pdel");
      addMessage("Список пресетов", "plist");
      addMessage("Использовать пресет: p [key]", "p");
      addMessage("Поменять ник: nick [nick]", "nick");
      addMessage("Очистить чат", "clear");
      addMessage("Перезагрузить чат", "reload");
      addMessage("Список серверов", "list");
      addMessage("Добавить сервер в список серверов: add ws(s)://[ip(:port)]", "add");
      addMessage("Удалить сервер из списка серверов: del [index]", "del");
      addMessage("Подключиться к серверу: con ws(s)://[ip(:port)]", "con");
      addMessage("Подключиться к серверу из списка: conl [index]", "conl");
      addMessage("Отключиться от сервера", "dcon");
      addMessage("Открыть конфиг MUCO", "config");
      addMessage("Открыть папку шрифтов", "fonts");
      addMessage("Перезапустить MUCO", "restart");
      addMessage("Выйти из MUCO", "exit");
    } else
    if (cmd[0] == "clear") {
      messages.value.splice(0, messages.value.length);
    } else
    if (cmd[0] == "padd") {
      let key = cmd[1];
      let preset = cmd.slice(2).join(' ');
      config.data.presets[key] = preset;
      saveConfig();
      addMessage(`Пресет '${key}' добавлен.`, "system");
    } else
    if (cmd[0] == "pdel") {
      let key = cmd[1];
      delete config.data.presets[key];
      saveConfig();
      addMessage(`Пресет '${key}' удален.`, "system");
    } else
    if (cmd[0] == "plist") {
      addMessage(`Всего ${Object.keys(config.data.presets).length} пресет(-ов):`, "system");
      let i = 0;
      for (let key of Object.keys(config.data.presets)) {
        addMessage(`#${i} - ${key}: ${config.data.presets[key].slice(0, 16)}...`, "system");
        i++;
      }
      if (Object.keys(config.data.presets).length == 0) {
        addMessage(` - нет пресетов`, "system");
      }
    } else
    if (cmd[0] == "p") {
      let key = cmd[1];
      let preset = config.data.presets[key];
      sendMessage(preset);
    } else
    if (cmd[0] == "reload") {
      api.getHistory();
    } else
    if (cmd[0] == "con") {
      addMessage(`Подключение к ${cmd[1]}...`, "system")
      connectedServer = cmd[1];
      api.connect(cmd[1]);
    } else
    if (cmd[0] == "nick") {
      let nick = cmd.slice(1).join(' ');
      config.data.nickname = nick;
      saveConfig();
      addMessage(`Ник изменен на '${nick}'.`, "system");
    } else
    if (cmd[0] == "add") {
      let server = cmd.slice(1).join(' ');
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
        connectedServer = server;
        addMessage(`Подключение к ${server}...`, "system")
        api.connect(server);
      } else {
        addMessage("Такого индекса нет в списке.", "system");
      }
    } else
    if (cmd[0] == "dcon") {
      api.disconnect();
    } else
    if (cmd[0] == "restart") {
      ipc.restartApp();
    } else
    if (cmd[0] == "config") {
      ipc.openConfigFolder();
    } else
    if (cmd[0] == "fonts") {
      ipc.openFontsFolder();
    } else
    if (cmd[0] == "exit") {
      if (wsService.socket) {api.disconnect();}
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
        addMessage(" - нет серверов", "system");
      }
    }
    else {
      addMessage(text, config.data.nickname);
    }
  }
}

function processWsData(data) {
  console.log(data);
  let content = data;
  if (content.type == "connaccept") {
    connected = true;
    checker = setInterval(checkOnline, 100);
    addMessage(`Подключено к серверу.`, "system");
    wsService.send({type: "getHistory"});
  } else if (content.type == "connmeta") {
    api.sendMeta();
  } else if (content.type == "connreject") {
    addMessage(`Ошибка подключения к серверу.`, "system");
    addMessage(` - ${content.error}`);
  } else if (content.type == "connclose") {
    addMessage(`Сервер закрыл подключение.`, "system");
    connected = false;
    connectedServer = "";
    checker.close();
  } else if (content.type == "history") {
    messages.value.splice(0, messages.value.length);
    addMessage("Чат очищен. Загружается история чата сервера...", "system");
    for (let msg of content.messages) {
      addMessage(msg.text, msg.author, msg.id);
    };
  } else if (content.type == "message") {
    addMessage(content.text, content.author, content.id);
  } else if (content.type == "dcon-agree") {
    addMessage("Отключено от сервера.", "system");
    connectedServer = "";
    connected = false;
    if (checker != null) {checker.close();}
  }
}

let chatTheme = computed(() => `
  background: ${currentTheme.value.base.basecolor};
  color: ${currentTheme.value.base.textcolor};
  font-family: ${currentTheme.value.base.font};
  font-size: ${currentTheme.value.base.fontsize};
  font-weight: ${currentTheme.value.base.fontboldness};
`);

onMounted(async () => {
  let mucover = await ipc.getVersion();
  addMessage(`MUCO ${mucover}`, "system");
  wsService.subscribe(processWsData);
  if (config.data.servers.length > 0 && config.data.autoConnectTo != -1) {
    wsService.connect(config.data.servers[config.data.autoConnectTo]);
  } else {
    addMessage("Чат не подключен к серверу.", "setup");
    addMessage("Для настройки MUCO стоит прочитать <a href='https://github.com/nesquikcode/multiuser-chat-overlay/wiki/%D0%9A%D0%BE%D0%BD%D1%84%D0%B8%D0%B3-muco.json' target='_blank'>wiki по конфигу</a>.", "setup")
    addMessage("Активные бинды:", "system");
    addMessage("  Enter - отправить сообщение", "system");
    addMessage(`  ${config.data.typeKeybinds.join(' ')} - переключить фокус чата`, "system");
    addMessage("Доп. команды: !help", "system");
    if (config.data.checkUpdates) {
      addMessage("Проверка обновлений...", "update")
      let updates = await ipc.checkUpdates()
      if (!updates.isUpToDate) {
        addMessage(`Доступна новая версия MUCO - ${updates.latest.version}.`, "update")
        if (config.data.autoUpdate) {
          addMessage("Скачиваем последнюю версию, MUCO перезапустится для обновления.", "update")
          ipc.updateToLatest()
        } else {
          addMessage(`Автообновление отключено. Скачать новую версию можно <a href='${updates.latest.link}' target='_blank'>вручную</a>.`, "update")
        }
      } else {
      addMessage("MUCO последней версии, обновлений не требуется.", "update")
      }
    }
  }
})
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
