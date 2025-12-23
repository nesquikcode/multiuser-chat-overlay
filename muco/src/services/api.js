import { version } from "dompurify";

export class MUCOAPI {
    constructor(wsService) {
        this.ws = wsService;
        this.protover = "0.1.32";
    }

    sendMeta() {
        this.ws.send({
            type: "connmeta",
            version: this.protover
        })
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