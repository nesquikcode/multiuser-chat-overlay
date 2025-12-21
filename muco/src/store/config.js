import { reactive } from 'vue'

export const config = reactive({
  ready: false,
  data: {
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
})

export async function loadConfig() {
  config.data = await window.config.get()
  config.ready = true
}

export async function saveConfig() {
  await window.config.set(config.data)
}
