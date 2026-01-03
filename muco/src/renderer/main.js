import { createApp } from 'vue'
import App from './App.vue'
import { loadConfig } from '@/renderer/store/config'

async function bootstrap() {
  await loadConfig()
  createApp(App).mount('#app')
}

bootstrap()