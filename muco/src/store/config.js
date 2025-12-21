import { reactive, toRaw } from 'vue';
import { ipc } from '@/services/ipc';

export const config = reactive({
    data: {},
    ready: false
});

export async function loadConfig() {
  config.data = await ipc.getConfig();
  config.ready = true;
}

export async function saveConfig() {
  await ipc.setConfig(toRaw(config.data));
}

export async function reloadConfig() {
  config.data = await ipc.getConfig()
}