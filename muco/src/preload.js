import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  onTypeEvent: (cb) => ipcRenderer.on('type-event', cb),
  onStopTypeEvent: (cb) => ipcRenderer.on('stop-type-event', cb)
})

contextBridge.exposeInMainWorld('config', {
  get: () => ipcRenderer.invoke('config:get'),
  set: (cfg) => ipcRenderer.invoke('config:set', cfg)
})
