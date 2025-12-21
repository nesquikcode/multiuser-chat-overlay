import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('ipc', {
  send: (channel, payload) =>
    ipcRenderer.send(channel, payload),

  invoke: (channel, payload) =>
    ipcRenderer.invoke(channel, payload),

  on(channel, callback) {
    const wrapped = (_, data) => callback(data)
    ipcRenderer.on(channel, wrapped)
    return () => ipcRenderer.removeListener(channel, wrapped)
  }
})
