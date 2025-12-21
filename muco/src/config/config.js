import fs from 'fs'
import path from 'path'
import { app } from 'electron'

const CONFIG_NAME = 'muco.json'
let cache = null

const defaultConfig = {
    height: 296,
    width: 384,
    nickname: "user",
    themes: {
        "dark" : {
            base: {
                basecolor: "rgba(18, 18, 18, 0.4)",
                textcolor: "rgba(255, 255, 255, 0.9)",
                font: "Arial, sans-serif",
                fontsize: "12px",
                fontboldness: "0"
            },
            message: {
                author: {
                    background: "none",
                    textcolor: "rgba(255, 255, 255, 0.9)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "400"
                },
                content: {
                    background: "none",
                    textcolor: "rgba(255, 255, 255, 0.9)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "0"
                }
            },
            input: {
                height: "24px",
                width: "100%",
                background: "rgba(18, 18, 18, 0.4)"
            }
        },
        "white" : {
            base: {
                basecolor: "rgba(255, 255, 255, 0.4)",
                textcolor: "rgba(0, 0, 0, 0.9)",
                font: "Arial, sans-serif",
                fontsize: "12px",
                fontboldness: "0"
            },
            message: {
                author: {
                    background: "none",
                    textcolor: "rgba(0, 0, 0, 0.9)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "400"
                },
                content: {
                    background: "none",
                    textcolor: "rgba(0, 0, 0, 0.9)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "0"
                }
            },
            input: {
                height: "24px",
                width: "100%",
                background: "rgba(255, 255, 255, 0.4)"
            }
        }
    },
    activeTheme: "dark",
    typeKeybinds: [
    "'"
    ],
    servers: [], // ip addresses like "ws://127.0.0.1:1111"
    autoConnectTo: -1 // index of server, connect on startup, -1 for ignoring
}

function getConfigPath() {
  return path.join(app.getPath('userData'), CONFIG_NAME)
}

export function loadConfig() {
  if (cache) return cache

  const configPath = getConfigPath()

  if (!fs.existsSync(configPath)) {
    fs.writeFileSync(
      configPath,
      JSON.stringify(defaultConfig, null, 2)
    )
    cache = structuredClone(defaultConfig)
    return cache
  }

  cache = JSON.parse(fs.readFileSync(configPath, 'utf-8'))
  return cache
}

export function saveConfig(newConfig) {
  const configPath = getConfigPath()
  cache = newConfig
  fs.writeFileSync(configPath, JSON.stringify(newConfig, null, 2))
}

export function getConfig() {
  return cache || loadConfig()
}
