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
                    textcolor: "rgba(255, 255, 255, 0.7)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "bold"
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
                color: "rgba(255, 255, 255, 0.4)"
            }
        },
        "white" : {
            base: {
                basecolor: "rgba(255, 255, 255, 0.4)",
                textcolor: "rgba(22, 22, 22, 0.9)",
                font: "Arial, sans-serif",
                fontsize: "12px",
                fontboldness: "0"
            },
            message: {
                author: {
                    background: "none",
                    textcolor: "rgba(22, 22, 22, 0.9)",
                    font: "Arial, sans-serif",
                    fontsize: "12px",
                    fontboldness: "bold"
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
                color: "rgba(18, 18, 18, 0.6)"
            }
        }
    },
    activeTheme: "dark",
    typeKeybinds: [
    "'"
    ],
    blurOnEnter: true,
    servers: [], // ip addresses like "ws://127.0.0.1:1111"
    autoConnectTo: -1, // index of server, connect on startup, -1 for ignoring
    autoReconnect: true,
    safeFormattingRender: true,
    presets: {},
    checkUpdates: true,
    autoUpdate: false
}

export function getConfigPath() {
    return path.join(app.getPath('userData'), CONFIG_NAME)
}

export function loadConfig() {
    if (cache) return cache

    const configPath = getConfigPath()
    let userConfig = {}

    if (fs.existsSync(configPath)) {
        userConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'))
    }

    const merged = deepMerge(defaultConfig, userConfig)

    if (JSON.stringify(userConfig) !== JSON.stringify(merged)) {
        fs.writeFileSync(configPath, JSON.stringify(merged, null, 2))
    }

    cache = merged
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

export function deepMerge(defaults, user) {
    const result = structuredClone(defaults)
    for (const key in user) {
    if (
        typeof user[key] === 'object' &&
        user[key] !== null &&
        !Array.isArray(user[key]) &&
        typeof defaults[key] === 'object'
    ) {
        result[key] = deepMerge(defaults[key], user[key])
    } else {
        result[key] = user[key]
    }
    }

    return result
}
