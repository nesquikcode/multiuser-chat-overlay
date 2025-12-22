export class MUCOAPI {
    constructor(wsService) {
        this.ws = wsService;
    }

    connect(url) {
        this.ws.connect(url);
    }

    getHistory() {
        this.ws.send({
            type: "getHistory"
        })
    }

    sendMessage(author, text) {
        this.ws.send({
            type: "message",
            text: text,
            author: author,
            id: Date.now()
        })
    }

    disconnect() {
        this.ws.send({
            type: "disconnect"
        })
    }
}