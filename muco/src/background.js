'use strict'

import fs from 'fs'
import path from 'path';
import { Parser } from 'rss-parser';
import { loadConfig, saveConfig, getConfig, getConfigPath } from './config/config'
import { app, protocol, BrowserWindow, globalShortcut, ipcMain, shell } from 'electron'
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer'
const isDevelopment = process.env.NODE_ENV !== 'production'

let focused = false;
let config = getConfig();

const fontsDir = path.join(app.getPath('userData'), 'fonts')
fs.mkdirSync(fontsDir, { recursive: true })

// Scheme must be registered before the app is ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true } }
])

async function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    width: config.width,
    height: config.height,
    frame: false,
    transparent: true,
    resizable: true,
    movable: true,
    alwaysOnTop: true,
    focused: true,
    hasShadow: false,
    webPreferences: {
      backgroundThrottling: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false,
      // Use pluginOptions.nodeIntegration, leave this alone
      // See nklayman.github.io/vue-cli-plugin-electron-builder/guide/security.html#node-integration for more info
      nodeIntegration: process.env.ELECTRON_NODE_INTEGRATION,
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION
    },
    additionalArguments: [
      `--fontsDir=${fontsDir}`
    ]
  })
  win.setAlwaysOnTop(true, "screen-saver");
  win.setVisibleOnAllWorkspaces(true);
  win.setFullScreenable(false);
  win.focus();

  for (const keyBind of config.typeKeybinds) {
    globalShortcut.register(keyBind, () => {
      if (win) {
        if (focused) {
          console.log("[event]: stop-type-event");
          win.webContents.send('stop-type-event');
          focused = false;
          win.show();
          win.blur();
        } else {
          console.log("[event]: type-event");
          win.webContents.send('type-event');
          focused = true;
          win.show();
          win.focus();
        }
      }
    });
  }

  ipcMain.on('window:blur', () => {
    console.log("[event]: stop-type-event");
    win.webContents.send('stop-type-event');
    focused = false;
    win.show();
    win.blur();
  })

  if (process.env.WEBPACK_DEV_SERVER_URL) {
    // Load the url of the dev server if in development mode
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL)
    if (!process.env.IS_TEST) win.webContents.openDevTools({mode: 'detach'})
  } else {
    createProtocol('app')
    // Load the index.html when not in development
    win.loadURL('app://./index.html')
  }
}

ipcMain.handle('window:getVersion', () => {
  return app.getVersion();
})

ipcMain.handle('fonts:list', () => {
  return fs
  .readdirSync(fontsDir)
  .filter(f => /\.(ttf|otf|woff2?)$/i.test(f))
  .map(file => ({
    name: path.parse(file).name,
    path: path.join(fontsDir, file)
  }))
})

ipcMain.handle('config:get', () => {
  return getConfig()
})

ipcMain.handle('config:set', (_, newConfig) => {
  saveConfig(newConfig)
  return true
})

ipcMain.on('app:restart', () => {
  app.relaunch()
  app.exit(0)
})

ipcMain.on('config:openFolder', () => {
  shell.openPath(getConfigPath())
})

ipcMain.on('config:fontsFolder', () => {
  shell.openPath(fontsDir)
})

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', async () => {
  if (isDevelopment && !process.env.IS_TEST) {
    // Install Vue Devtools
    try {
      await installExtension(VUEJS3_DEVTOOLS)
    } catch (e) {
      console.error('Vue Devtools failed to install:', e.toString())
    }
  }
  createWindow()
})

// Exit cleanly on request from parent process in development mode.
if (isDevelopment) {
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}