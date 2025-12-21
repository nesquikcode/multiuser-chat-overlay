import { onMounted, onBeforeUnmount } from 'vue'
import { ipc } from '@/services/ipc'

export function useTypeEvents({ onType, onStop }) {
  let offType = null
  let offStop = null

  onMounted(() => {
    offType = ipc.onTypeEvent(onType)
    offStop = ipc.onStopTypeEvent(onStop)
  })

  onBeforeUnmount(() => {
    offType?.()
    offStop?.()
  })
}
