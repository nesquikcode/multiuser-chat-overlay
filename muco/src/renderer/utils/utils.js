import { ipc } from "@/renderer/services/ipc";

export function getByKey(obj, path, defaultValue = undefined) {
  return path
    .split('.')
    .reduce((o, key) => (o ? o[key] : undefined), obj) ?? defaultValue;
}

export function setByKey(obj, path, value) {
  const keys = path.split('.');
  keys.reduce((o, key, i) => {
    if (i === keys.length - 1) {
      o[key] = value;
    } else if (!o[key] || typeof o[key] !== 'object') {
      o[key] = {};
    }
    return o[key];
  }, obj);
}

export async function checkUpdates(chat) {
  chat.addMessage("Проверка обновлений...", "update")
  let updates = await ipc.checkUpdates()
  if (updates.isUpToDate) {
    chat.addMessage("MUCO последней версии, обновлений не требуется.", "update")
  } else {
    chat.addMessage(`Доступна новая версия MUCO - ${updates.latest.version}.`, "update")
    if (config.data.autoUpdate) {
      chat.addMessage("Скачиваем последнюю версию, MUCO перезапустится для обновления.", "update")
      ipc.updateToLatest()
    } else {
      chat.addMessage(`Автообновление отключено. Скачать новую версию можно <a href='${updates.latest.link}' target='_blank'>вручную</a>.`, "update")
    }
  }
}

export function checkOnline(data) {
  if (data.isConnected && (data.wsService.socket == null)) {
    data.chat.addMessage("Отключено от сервера.", "system");
    data.isConnected = false;

    if (data.config.data.autoReconnect) {
      data.chat.addMessage("Переподключение к серверу...", "system");
      data.wsService.connect(data.connectedTo);
    } else {
      data.connectedTo = null;
    }
  }
}

export function removePrefix(str, prefix) {
  return str.startsWith(prefix) ? str.slice(prefix.length) : str;
}