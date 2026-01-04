import { checkOnline } from "@/renderer/utils/utils";
import { saveConfig } from "@/renderer/store/config";

export class MUCOAPI {
    constructor() {}

    connmeta(nick, protover, uuid) {
        return {
            type: "connmeta",
            nickname: nick,
            version: protover,
            uuid: uuid
        }
    }

    connaccept(uuid) {
        return {
            type: "connaccept",
            uuid: uuid
        }
    }

    connreject(uuid, reason) {
        return {
            type: "connreject",
            error: reason,
            uuid: uuid
        }
    }

    connclose(uuid) {
        return {
            type: "connclose",
            uuid: uuid
        }
    }

    disconnect(uuid) {
        return {
            type: "disconnect",
            uuid: uuid
        }
    }

    dconagree(uuid) {
        return {
            type: "dcon-agree",
            uuid: uuid
        }
    }

    message(text, author, id, uuid) {
        return {
            type: "message",
            text: text,
            author: author,
            id: id,
            uuid: uuid
        }
    }

    privateMessage(text, author, touser, id, uuid) {
        return {
            type: "privateMessage",
            text: text,
            author: author,
            touser: touser,
            id: id,
            uuid: uuid
        }
    }

    getHistory(uuid, from) {
        if (from == undefined) {
            return {
                type: "getHistory",
                uuid: uuid
            }
        } else {
            return {
                type: "getHistory",
                from: from,
                uuid: uuid
            }
        }
    }

    history(uuid, messages) {
        return {
            type: "history",
            messages: messages
        }
    }

    nickchange(uuid, nick) {
        return {
            type: "nickchange",
            uuid: uuid,
            nickname: nick
        }
    }
}

export class MUCOData {
    constructor(wsService, config) {
        this.chat = null;
        this.wsService = wsService;
        this.api = new MUCOAPI();

        this.config = config;
        this.protover = "0.1.7";

        this.clientUUID = crypto.randomUUID();
        this.serverUUID = null;
        this.connectedTo = null;
        this.isConnected = false;
        this.checker = null;
    }
}

export class MUCOSender {
    constructor(data) {
        this.ws = data.wsService;
        this.cfg = data.config;
        this.uuid = data.clientUUID;
        this.data = data;
    }

    connect(url) {
        this.ws.connect(url);
        this.data.connectedTo = url;
    }

    sendMessage(author, text) {
        this.ws.send(
            this.data.api.message(
                text,
                author,
                Date.now(),
                this.data.clientUUID
            )
        )
    }

    sendPrivateMessage(author, touser, text) {
        this.ws.send(
            this.data.api.privateMessage(
                text,
                author,
                touser,
                Date.now(),
                this.data.clientUUID
            )
        )
    }

    getHistory() {
        if (this.cfg.data.loadServerHistoryFrom > 0) {
            this.ws.send(
                this.data.api.getHistory(
                    this.data.clientUUID,
                    this.cfg.data.loadServerHistoryFrom
                )
            )
        } else {
            this.ws.send(
                this.data.api.getHistory(
                    this.data.clientUUID
                )
            )
        }
    }

    changeNickname(nick) {
        this.ws.send(
            this.data.api.nickchange(this.data.clientUUID, nick)
        )
    }

    disconnect() {
        this.ws.send(
            this.data.api.disconnect(this.data.clientUUID)
        )
    }
}

export class MUCOReceiver {
    constructor(data) {
        this.ws = data.wsService;
        this.config = data.config;
        this.data = data;

        this.ws.subscribe((data) => {this.dataHandler(data)});

        this.audio = null;
        if (this.config.data.onMessageSound != null) {
            this.audio = new Audio();
            this.audio.src = this.config.data.onMessageSound;
            this.audio.load();
            console.log("[audio]: onMessage initialized:", this.audio)
        }
    }

    connmetaHandler(packet) {
        console.log(`[receiver]: Got server-side connmeta, serverUUID is ${packet.uuid}`);
        this.data.serverUUID = packet.uuid;
        this.ws.send(
            this.data.api.connmeta(
                this.config.data.nickname,
                this.data.protover,
                this.data.clientUUID
            )
        )
    }

    connacceptHandler(packet) {
        this.data.isConnected = true;
        this.data.checker = setInterval(() => {checkOnline(this.data)}, 100);
        this.data.chat.addMessage(`Подключено к серверу.`, "system");
        if (this.config.data.loadServerHistoryFrom > 0) {
            this.ws.send(
                this.data.api.getHistory(
                    this.data.clientUUID,
                    this.config.data.loadServerHistoryFrom
                )
            )
        } else {
            this.ws.send(
                this.data.api.getHistory(
                    this.data.clientUUID
                )
            )
        }
    }

    connrejectHandler(packet) {
        this.data.chat.addMessage(`Ошибка подключения к ${this.data.connectedTo}.`, "system");
        this.data.chat.addMessage(`- ${packet.error}`, "system");
        this.data.serverUUID = null;
        this.data.connectedTo = null;
        this.data.checker = null;
    }

    conncloseHandler(packet) {
        this.data.chat.addMessage(`Сервер закрыл подключение.`, "system");
        this.data.isConnected = false;
        this.data.checker = null;
        this.data.connectedTo = null;
        this.data.serverUUID = null;
    }

    historyHandler(packet) {
        this.data.chat.clear();
        if (packet.messages.length > this.config.data.maxVisibleMessages) {
            packet.messages = packet.messages.slice(-this.config.data.maxVisibleMessages)
        }

        this.data.chat.addMessage("Чат очищен. Загружается история чата сервера...", "system");
        for (let msg of packet.messages) {
            this.data.chat.addMessage(msg.text, msg.author, msg.id);
        };
    }

    messageHandler(packet) {
        this.data.chat.addMessage(packet.text, packet.author, packet.id);
        if (this.audio != null && this.data.wsService.lastsent != packet.id) {
            console.log(this.data.wsService.lastsent, packet.id)
            if (!this.audio.paused && !this.audio.ended && this.audio.currentTime > 0) {
                this.audio.pause();
                this.audio.currentTime = 0;
            }
            this.audio.play();
        }
    }

    dconagreeHandler(packet) {
        this.data.chat.addMessage("Отключено от сервера.", "system");
        this.data.isConnected = false;
        this.data.checker = null;
        this.data.connectedTo = null;
        this.data.serverUUID = null;
    }

    nickchangeHandler(packet) {
        this.config.data.nickname = packet.nickname;
        saveConfig();
        this.data.chat.addMessage(`Ник изменен на '${packet.nickname}'.`, "system");
    }

    dataHandler(data) {
        let packet = data;
        if (this.serverUUID != null && this.serverUUID != content.uuid) {
            console.log(`[receiver]: Ignoring packet '${content.type}' with UUID mismatch: server UUID - ${serverUUID}, got - ${content.uuid}`);
            return;
        }

        console.log(`[receiver]: Received '${packet.type}' packet:`, packet)
        switch (packet.type) {
            case 'connmeta': this.connmetaHandler(packet); break;
            case 'connaccept': this.connacceptHandler(packet); break;
            case 'connreject': this.connrejectHandler(packet); break;
            case 'connclose': this.conncloseHandler(packet); break;
            case 'history': this.historyHandler(packet); break;
            case 'message': this.messageHandler(packet); break;
            case 'dcon-agree': this.dconagreeHandler(packet); break;
            case 'nickchange': this.nickchangeHandler(packet); break;
            default: console.log(`[receiver]: Unknown packet type '${packet.type}'.`)
        }
    }
}