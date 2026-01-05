import { ipc } from "@/renderer/services/ipc";
import { saveConfig } from "@/renderer/store/config";
import { getByKey, setByKey, checkUpdates, removePrefix } from "@/renderer/utils/utils";

export class Chat {
    constructor(sender, config, ws, messages) {
        this.sender = sender;
        this.config = config;
        this.messages = messages;
        this.ws = ws;
        this.cmdhandler = new CommandHandler(this, this.config)
    }

    sendPrivateMessage(author, touser, text) {
        this.sender.sendPrivateMessage(author, touser, text);
    }

    sendMessage(text) {
        if (text == null) {return;}
        if (this.config.data.blurOnEnter) {ipc.blurWindow();}
        if (this.ws.socket && !text.startsWith(this.config.data.commandPrefix)) {
            this.sender.sendMessage(this.config.data.nickname, text);
        } else if (text.startsWith(this.config.data.commandPrefix)) {
            this.cmdhandler.exec(text);
        } else {
            this.addMessage(text, this.config.data.nickname);
        }
    }

    addMessage(text, author = this.config.data.nickname, id = Date.now()) {
        this.messages.value.push({
            id: id,
            text,
            author: author
        });
        if (this.messages.value.length > this.config.maxVisibleMessages) {
            this.messages.value.shift();
        }
    }

    clear() {
        this.messages.value.splice(0, this.messages.value.length);
    }
}

class CommandHandler {
    constructor(chat, config) {
        this.chat = chat;
        this.config = config;
    }

    helpHandler() {
        this.chat.addMessage("[описание]", "[команда]");
        this.chat.addMessage("Список команд", "help");
        this.chat.addMessage("Отправить личное сообщение: to [user] [text]", "to");
        this.chat.addMessage("Добавить текст в пресеты: padd [key] [text]", "padd");
        this.chat.addMessage("Удалить текст из пресетов: pdel [key]", "pdel");
        this.chat.addMessage("Список пресетов", "plist");
        this.chat.addMessage("Использовать пресет: p [key]", "p");
        this.chat.addMessage("Поменять ник: nick [nick]", "nick");
        this.chat.addMessage("Очистить чат", "clear");
        this.chat.addMessage("Перезагрузить чат", "reload");
        this.chat.addMessage("Список серверов", "list");
        this.chat.addMessage("Добавить сервер в список серверов: add ws(s)://[ip(:port)]", "add");
        this.chat.addMessage("Удалить сервер из списка серверов: del [index]", "del");
        this.chat.addMessage("Подключиться к серверу: con ws(s)://[ip(:port)]", "con");
        this.chat.addMessage("Подключиться к серверу из списка: conl [index]", "conl");
        this.chat.addMessage("Отключиться от сервера", "dcon");
        this.chat.addMessage("Управление конфигом", "config");
        this.chat.addMessage("Проверить обновления MUCO", "updates");
        this.chat.addMessage("Обновить MUCO до последней версии", "upgrade");
        this.chat.addMessage("Открыть папку шрифтов", "fonts");
        this.chat.addMessage("Перезапустить MUCO", "restart");
        this.chat.addMessage("Выйти из MUCO", "exit");
    }

    toHandler(args) {
        if (args.length < 2) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        let touser = args[0];
        let text = args.slice(1).join(' ');
        this.chat.sendPrivateMessage(this.config.data.nickname, touser, text);
    }
    
    paddHandler(args) {
        if (args.length < 2) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        let key = args[0];
        let preset = args.slice(1).join(' ');
        this.config.data.presets[key] = preset;
        saveConfig();
        this.chat.addMessage(`Пресет '${key}' добавлен.`, "system");
    }

    pdelHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
    
        let key = args[0];
        delete this.config.data.presets[key];
        saveConfig();
        this.chat.addMessage(`Пресет '${key}' удален.`, "system");
    }

    plistHandler() {
        this.chat.addMessage(`Всего ${Object.keys(this.config.data.presets).length} пресет(-ов):`, "system");
        let i = 0;
        for (let key of Object.keys(this.config.data.presets)) {
            this.chat.addMessage(`#${i} - ${key}: ${this.config.data.presets[key].slice(0, 16)}...`, "system");
            i++;
        }
        if (Object.keys(this.config.data.presets).length == 0) {
            this.chat.addMessage(` - нет пресетов`, "system");
        }
    }

    pHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        let key = args[0];
        let preset = this.config.data.presets[key];
        this.chat.sendMessage(preset);
    }

    conHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        this.chat.addMessage(`Подключение к ${args[0]}...`, "system")
        this.chat.sender.connect(args[0]);
    }

    nickHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
       
        let nick = args.join(' ');

        if (this.chat.sender.data.serverUUID == null) {
            this.config.data.nickname = nick;
            saveConfig();
            this.chat.addMessage(`Ник изменен на '${nick}'.`, "system");
        } else {
            this.chat.sender.changeNickname(nick);
        }
    }

    addHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        let server = args.join(' ');
        this.config.data.servers.push(server);
        saveConfig();
        this.chat.addMessage(`Добавлен сервер ${server}.`, "system");
    }

    delHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        let serverIndex = args[0];
        let server = this.config.data.servers[serverIndex];
        this.config.data.servers.splice(serverIndex, 1);
        saveConfig();
        this.chat.addMessage(`Удален сервер ${server}.`, "system");
    }

    conlHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        
        let server = this.config.data.servers.at(Number(args[0]));
        if (server) {
            this.chat.addMessage(`Подключение к ${server}...`, "system")
            this.chat.sender.connect(server);
        } else {
            this.chat.addMessage("Такого индекса нет в списке.", "system");
        }
    }

    configHandler(args) {
        if (args.length < 1) {this.chat.addMessage("Некорректное использование команды.", "system"); return}
        else if (args.length == 1 && args[0] == "open") {
            ipc.openConfigFolder(); return
        }
        
        let type = args[0];
        let setting = args[1];
        let value;
        let joined;
        if (args.length > 2) {value = args.slice(2); joined = value.join(' ')} else {value = ""; joined = ""}
        
        let settingValue = getByKey(this.config.data, setting);
        if (Array.isArray(settingValue)) {
            if (type == "set") {
                setByKey(this.config.data, setting, joined)
                this.chat.addMessage(`Значение списка ${setting} изменено на [${value.join(', ')}].`, "system")
            } else if (type == "add") {
                let arr = getByKey(this.config.data, setting, [])
                arr.push(joined)
                setByKey(this.config.data, setting, arr)
                this.chat.addMessage(`В список ${setting} добавлено '${joined}'.`, "system")
            } else if (type == "pop") {
                let arr = getByKey(this.config.data, setting, [])
                let el = arr.pop()
                setByKey(this.config.data, setting, arr)
                this.chat.addMessage(`Из списка ${setting} удалено '${el}'.`, "system")
            } else {
                this.chat.addMessage(`Для списка ${setting} нельзя использовать '${type}'.`, "system")
            }
        } else if (typeof settingValue == "string") {
            if (type == "set") {
                setByKey(this.config.data, setting, joined)
                this.chat.addMessage(`Значение строки ${setting} изменено на '${joined}'.`, "system")
            } else {
                this.chat.addMessage(`Для строки ${setting} нельзя использовать '${type}'.`, "system")
            }
        } else if (typeof settingValue == "number") {
            if (type == "set") {
                setByKey(this.config.data, setting, Number(joined))
                this.chat.addMessage(`Значение числа ${setting} изменено на '${Number(joined)}'.`, "system")
            } else if (type == "add") {
                setByKey(this.config.data, setting, settingValue + Number(joined))
                this.chat.addMessage(`Значение числа ${setting} изменено на '${Number(joined)}'.`, "system")
            } else if (type == "sub") {
                setByKey(this.config.data, setting, Number(joined) - settingValue)
                this.chat.addMessage(`Значение числа ${setting} изменено на '${Number(joined)}'.`, "system")
            } else {
                this.chat.addMessage(`Для числа ${setting} нельзя использовать '${type}'.`, "system")
            }
        } else if (typeof settingValue == "boolean") {
            if (type == "set") {
                setByKey(this.config.data, setting, Boolean(settingValue).valueOf())
                this.chat.addMessage(`Значение ${setting} изменено на '${B(joined)}'.`, "system")
            } else if (type == "toggle") {
                setByKey(this.config.data, setting, !Boolean(settingValue).valueOf())
                this.chat.addMessage(`Значение ${setting} изменено на '${settingValue}'.`, "system")
            } else {
                this.chat.addMessage(`Для ${setting} нельзя использовать '${type}'.`, "system")
            }
        } else if (typeof settingValue == "object") {
            let parsed;
            try {parsed = JSON.parse(value.join(' '))} catch {
                this.chat.addMessage("Значение некорректно.", "system"); return
            }
            if (type == "set") {
                setByKey(this.config.data, setting, parsed);
                this.chat.addMessage(`Значение объекта ${setting} изменено на '${joined}'.`, "system")
            } else {
                this.chat.addMessage(`Для объекта ${setting} нельзя использовать '${type}'.`, "system")
            }
        } else {
            this.chat.addMessage("Получен некорректный тип значения в конфиге.", "system");
        }
        saveConfig();
    }

    listHandler() {
        this.chat.addMessage("Список серверов:", "system");
        let i = 0;
        for (let server of this.config.data.servers) {
            this.chat.addMessage(`#${i} - ${server}`, "system");
            i++;
        }
        if (this.config.data.servers.length == 0) {
            this.chat.addMessage(" - нет серверов", "system");
        }
    }

    async upgradeHandler() {
        this.chat.addMessage("Проверка обновлений...", "update");
        let updates = await ipc.checkUpdates();
        if (updates.isUpToDate) {
            this.chat.addMessage("Нет обновлений.", "update");
        } else {
            this.chat.addMessage(`Скачиваем и устанавливаем MUCO ${updates.latest.version}...`, "update");
            ipc.updateToLatest();
        }
    }

    exec(text) {
        let cmd = removePrefix(text, this.config.data.commandPrefix).split(' ')
        let name = cmd[0]
        let args;
        if (cmd.length > 1) {
            args = cmd.slice(1, cmd.length)
        } else {args = [];}

        switch (name) {
            case 'help': this.helpHandler(); break;
            case 'to': this.toHandler(args); break;
            case 'clear': this.chat.clear(args); break;
            case 'padd': this.paddHandler(args); break;
            case 'pdel': this.pdelHandler(args); break;
            case 'plist': this.plistHandler(); break;
            case 'p': this.pHandler(args); break;
            case 'reload': this.chat.sender.getHistory(); break;
            case 'con': this.conHandler(args); break;
            case 'nick': this.nickHandler(args); break;
            case 'add': this.addHandler(args); break;
            case 'del': this.delHandler(args); break;
            case 'list': this.listHandler(); break;
            case 'conl': this.conlHandler(args); break;
            case 'dcon': this.chat.sender.disconnect(); break;
            case 'restart': ipc.restartApp(); break;
            case 'config': this.configHandler(args); break;
            case 'updates': checkUpdates(this.chat); break;
            case 'upgrade': this.upgradeHandler(); break;
            case 'fonts': ipc.openFontsFolder(); break;
            case 'exit': if (this.chat.ws.socket) {this.chat.sender.disconnect()}; window.close(); break;
            default: this.chat.addMessage("Неизвестная команда.", "system");
        }
    }
}