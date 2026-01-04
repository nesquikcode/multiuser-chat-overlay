from core import ConnectionClose, ConnectionReject, DisconnectionAgree, NicknameChange, Packet, Message, History, ConnectionAccept, ConnectionMeta, ClientData

import json, time, uuid, os, traceback, socket, logging

from queue import SimpleQueue
from logging.handlers import QueueHandler, QueueListener
from datetime import datetime
from aiofiles import open as asyncopen
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
os.chdir(os.path.dirname(__file__))
__version__ = "0.1.71"

log_queue = SimpleQueue()
queue_handler = QueueHandler(log_queue)
loghandler = logging.StreamHandler()
listener = QueueListener(log_queue, loghandler)
listener.start()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(queue_handler)

class ServerConfig(BaseModel):
    ip: str = "0.0.0.0"
    port: int = 5656
    server_size: int = 256
    server_nickname: str = "server"
    server_message_size: int = 8192
    server_history_size: int = 1024
    server_path: str = "/"
    certs: tuple | None = None
    allow_client_version: str = __version__

    @staticmethod
    def load(file: str = 'muco-server.json'):

        if os.path.exists(file):
            with open(file, "rt", encoding="utf-8") as f:
                data = f.read()
        else:
            cfg = ServerConfig()
            cfg.save()
            return cfg
        
        return ServerConfig(
            **json.loads(data)
        )
    
    def save(self, file: str = 'muco-server.json'):
        with open(file, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.model_dump(), indent=4))

messages = []
connecting: set[ClientData] = set()
clients: set[ClientData] = set()
config = ServerConfig.load()

def log(prefix: str, text: str):
    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}][{prefix}]: {text}")

async def lifespan(app: FastAPI):
    log("init", f"Starting MUCO Server ({__version__}) with config:")
    log("init", f" - ip: {config.ip}")
    log("init", f" - port: {config.port}")
    log("init", f" - server_size: {config.server_size}")
    log("init", f" - server_message_size: {config.server_message_size}")
    log("init", f" - server_history_size: {config.server_history_size}")
    log("init", f" - server_nickname: {config.server_nickname}")
    log("init", f" - server_path: {config.server_path}")
    log("init", f" - allow_client_version: {config.allow_client_version}")
    log("init", f" - tls (certs): {'enabled' if config.certs is not None else 'disabled'}")

    serverip = socket.gethostbyname(socket.gethostname())
    log("init", f"Server is available using this link: ws{'s' if config.certs is not None else ''}://{serverip}:{config.port}{config.server_path}")
    yield
    log("shutdown", "Shutting down MUCO Server...")

    for x in connecting:
        await x.ws.send_text(
            ConnectionClose(
                x.server_uuid
            ).wsPacket
        )
        await x.ws.close()

    for x in clients:
        await x.ws.send_text(
            ConnectionClose(
                x.server_uuid
            ).wsPacket
        )
        await x.ws.close()
    
    config.save()
    
    log("shutdown", "Bye!")

app = FastAPI(
    title="MUCO WebSocket Server",
    version=__version__,
    lifespan=lifespan
)

async def broadcast(text: str, author: str, id: int):
    for x in clients.copy():
        if x.ws.client_state == WebSocketState.DISCONNECTED:
            clients.discard(x)
        else:
            await x.ws.send_text(
                Message(
                    x.server_uuid,
                    text,
                    author,
                    id
                ).wsPacket
            )

@app.websocket(config.server_path)
async def handler(ws: WebSocket):
    await ws.accept()

    server_uuid = uuid.uuid4().__str__()
    await ws.send_text(
        ConnectionMeta(
            server_uuid,
            config.allow_client_version,
            config.server_nickname
        ).wsPacket
    )

    log("handler::preconn", f"New connection. Sent connmeta and generated server uuid: {server_uuid}.")

    try:
        while True:
            data = json.loads(await ws.receive_text())
            datatype = data.get("type")
            client_uuid = data.get("uuid")

            if datatype is None:
                await ws.close(1000, "unknown packet type")
                break
            elif client_uuid is None:
                log("handler::conn", "No UUID in packet. Rejecting and closing connection.")
                await ws.send_text(
                    ConnectionReject(
                        server_uuid,
                        "uuid required"
                    ).wsPacket
                )
                await ws.close()
                break
            
            client = None
            for x in connecting.copy():
                if x.ws == ws and x.client_uuid == client_uuid:
                    client = x
                    break
            else:
                for x in clients.copy():
                    if x.ws == ws and x.client_uuid == client_uuid:
                        client = x
                        break

            if client is None:
                log("handler::conn", f"Unknown client detected. Processing to new client: {client_uuid} / {server_uuid}.")
                client = ClientData(
                    ws,
                    client_uuid,
                    server_uuid
                )
                connecting.add(client)
            
            data.pop("type")
            data.pop("uuid")
            packet = Packet(datatype, client_uuid, **data)

            if client in connecting:
                if packet.type == "connmeta":
                    log("handler::connmeta", f"Got connmeta from {client.client_uuid} client.")
                    
                    for x in clients:
                        if x.nickname == packet["nickname"]:
                            log("handler::connmeta", f"Client {client.client_uuid} using same nickname as {x.client_uuid}. Rejecting connection.")
                            await ws.send_text(
                                ConnectionReject(
                                    client.server_uuid,
                                    "nickname already taken, change nickname"
                                ).wsPacket
                            )
                            await ws.close()
                            break
                    
                    if packet["version"] == config.allow_client_version:
                        log("handler::connmeta", f"Client {client.client_uuid} using allowed version. Accepting connection.")
                        await ws.send_text(
                            ConnectionAccept(
                                server_uuid
                            ).wsPacket
                        )
                        connecting.discard(client)

                        client.nickname = packet["nickname"]
                        clients.add(client)
                    else:
                        log("handler::connmeta", f"Client {client.client_uuid} using wrong version - {packet['version']} ({config.allow_client_version} allowed). Rejecting connection.")
                        connecting.discard(client)
                        await ws.send_text(
                            ConnectionReject(
                                server_uuid,
                                f"version mismatch: client is {packet['version']}, server is {config.allow_client_version}"
                            ).wsPacket
                        )
                        await ws.close()
                        break
                else:
                    log("handler::connmeta", f"Client {client.client_uuid} sent unknown packet type - {packet.type}. Closing connection.")
                    connecting.discard(client)
                    await ws.send_text(
                        ConnectionClose(
                            server_uuid
                        ).wsPacket
                    )
                    await ws.close()
            
            else:
                if packet.type == "getHistory":
                    log("handler::getHistory", f"Client {client.client_uuid} requested server history.")
                    await ws.send_text(
                        History(
                            server_uuid,
                            messages
                        ).wsPacket
                    )
                elif packet.type == "message":
                    log("handler::message", f"Client {client.client_uuid} sent a message.")

                    if packet["author"] == config.server_nickname:
                        log("handler::message", f"Client's ({client.client_uuid}) message rejected for using server nickname - {packet['author']}.")
                        await ws.send_text(
                            Message(
                                client.server_uuid,
                                f"Имя '{config.server_nickname}' является серверным. Его нельзя использовать.",
                                config.server_nickname,
                                int(time.time())
                            ).wsPacket
                        )
                    
                    elif len(packet["text"]) > config.server_message_size:
                        log("handler::message", f"Client's ({client.client_uuid}) message too big - {len(packet['text'])}, max allowed is {config.server_message_size}.")
                        await ws.send_text(
                            Message(
                                client.server_uuid,
                                f"Сообщение слишком большое (>{config.server_message_size}).",
                                config.server_nickname,
                                int(time.time())
                            ).wsPacket
                        )

                    else:
                        log(f"chat / {client.client_uuid}::{client.nickname}", f"{packet['text']}")
                        messages.append(packet.content)
                        if len(messages) > config.server_history_size:
                            messages.pop(0)
                        
                        await broadcast(
                            packet["text"],
                            client.nickname,
                            packet["id"]
                        )
                
                elif packet.type == "privateMessage":
                    log("handler::privateMessage", f"Client {client.client_uuid} requested private message ('{packet['author']}'->'{packet['touser']}').")

                    if config.server_nickname in [packet['author'], packet['touser']]:
                        log("handler::privateMessage", f"Client's ({client.client_uuid}) private message rejected for using server nickname.")
                        await ws.send_text(
                            Message(
                                client.server_uuid,
                                f"Имя '{config.server_nickname}' является серверным. Его нельзя использовать.",
                                config.server_nickname,
                                int(time.time())
                            ).wsPacket
                        )
                    
                    else:
                        touser = None
                        for x in clients:
                            if x.nickname == packet["touser"]:
                                touser = x
                                break
                        
                        if touser is None:
                            log("handler::privateMessage", f"Client's ({client.client_uuid}) private message can't delivered, touser is unknown client.")
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    f"Пользователь '{packet['touser']}' не найден.",
                                    config.server_nickname,
                                    int(time.time())
                                ).wsPacket
                            )
                        else:
                            log(f"privateChat / {client.client_uuid}::{client.nickname}->{touser.nickname}", f"{packet['text']}")
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    packet["text"],
                                    f"{client.nickname} -> {touser.nickname}",
                                    int(time.time())
                                ).wsPacket
                            )
                            await touser.ws.send_text(
                                Message(
                                    client.server_uuid,
                                    packet["text"],
                                    f"{touser.nickname} <- {client.nickname}",
                                    int(time.time())
                                ).wsPacket
                            )
                
                elif packet.type == "disconnect":
                    log("handler::disconnect", f"Client {client.client_uuid} disconnected.")
                    clients.discard(client)
                    await ws.send_text(
                        DisconnectionAgree(
                            client.server_uuid
                        ).wsPacket
                    )
                    await ws.close()
                    break

                elif packet.type == "nickchange":
                    log("handler::disconnect", f"Client {client.client_uuid} requested nickname change ({client.nickname}->{packet['nickname']}).")

                    for x in clients:
                        if x.nickname == packet['nickname']:
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    "Ник уже используется другим пользователем.",
                                    config.server_nickname,
                                    int(time.time())
                                ).wsPacket
                            )
                            break
                    else:
                        client.nickname = packet['nickname']
                        await ws.send_text(
                            NicknameChange(
                                client.server_uuid,
                                packet['nickname']
                            ).wsPacket
                        )
    
    except WebSocketDisconnect:
        log("handler::info", "Websocket disconnected, discarding client.")
        for client in clients.copy():
            if ws == client.ws:
                clients.discard(client)
                break

    except Exception as e:
        log("handler::err", f"Got exception: {e}")
        async with asyncopen(f"exception-{int(time.time())}.log", "w") as f:
            await f.write(f"Error log on {datetime.now().strftime('%d-%m-%y at %H:%M:%S')}.\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    from uvicorn import Server, Config

    if config.certs is None:
        cfg = Config(
            app,
                config.ip,
                config.port,
                workers=1
            )
    else:
        cfg = Config(
            app,
                config.ip,
                config.port,
                workers=1,
                ssl_certfile=config.certs[0],
                ssl_keyfile=config.certs[1],
                access_log=False
            )
    
    server = Server(cfg)

    try:
        server.run()
    except KeyboardInterrupt:
        server.should_exit = True