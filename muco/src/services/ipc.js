export const ipc = {
    getConfig() {
        return window.ipc.invoke('config:get')
    },

    setConfig(cfg) {
        return window.ipc.invoke('config:set', cfg)
    },

    onTypeEvent(cb) {
        return window.ipc.on('type-event', cb)
    },

    onStopTypeEvent(cb) {
        return window.ipc.on('stop-type-event', cb)
    },

    restartApp() {
        window.ipc.send('app:restart')
    },

    openConfigFolder() {
        window.ipc.send('config:openFolder')
    }
}
