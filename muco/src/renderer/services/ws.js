class WSService {
  socket = null
  listeners = new Set()
  lastsent = 0;

  connect(url) {
    if (this.socket) return

    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      console.log('[wsService]: Connected.')
    }

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.listeners.forEach(cb => cb(data))
    }

    this.socket.onclose = () => {
      console.log('[wsService]: Connection closed.')
      this.socket = null
    }

    this.socket.onerror = (e) => {
      console.error('[wsService]: Got websocket error:', e)
    }
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log(`[ws::send]: Sending '${data.type}' packet:`, data)
      this.socket.send(JSON.stringify(data))
      if ((data.id != undefined && data.id != null) && typeof data.id == "number") {
        this.lastsent = data.id;
      }
    }
  }

  subscribe(cb) {
    this.listeners.add(cb)
    return () => this.listeners.delete(cb)
  }
}

export const wsService = new WSService()
