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
    },

    blurWindow() {
        window.ipc.send('window:blur')
    },

    getFonts() {
        return window.ipc.invoke('fonts:list')
    },

    openFontsFolder() {
        window.ipc.send('config:fontsFolder')
    },

    getVersion() {
        return window.ipc.invoke('window:getVersion')
    },

    checkUpdates() {
        return window.ipc.invoke('window:checkUpdates')
    },

    updateToLatest() {
        window.ipc.send('window:updateToLatest')
    }
}
