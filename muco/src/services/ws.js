class WSService {
  socket = null
  listeners = new Set()

  connect(url) {
    if (this.socket) return

    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      console.log('[WS] connected')
    }

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.listeners.forEach(cb => cb(data))
    }

    this.socket.onclose = () => {
      console.log('[WS] closed')
      this.socket = null
    }

    this.socket.onerror = (e) => {
      console.error('[WS] error', e)
    }
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data))
    }
  }

  subscribe(cb) {
    this.listeners.add(cb)
    return () => this.listeners.delete(cb)
  }
}

export const wsService = new WSService()
