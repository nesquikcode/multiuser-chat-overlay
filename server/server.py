import asyncio
import base64
import hashlib
import importlib.util
from collections import deque
from core import ConnectionClose, ConnectionReject, DisconnectionAgree, NicknameChange, Packet, Message, History, ConnectionAccept, ConnectionMeta, ClientData

import json, time, uuid, os, traceback, socket, logging, importlib, sys

import logging
from queue import SimpleQueue
from logging.handlers import QueueHandler, QueueListener
from datetime import datetime
from aiofiles import open as asyncopen
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from fastapi.responses import FileResponse, Response
from bs4 import BeautifulSoup
os.chdir(os.path.dirname(__file__))
__version__ = "0.1.71"

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
    allow_server_actual_version: bool = True
    plugins_directory: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "plugins"))
    errorlog_directory: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "errors"))
    cache_directory: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "cache"))
    log_level: int = logging.INFO

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

config = ServerConfig.load()
messages: deque[dict] = deque(maxlen=config.server_history_size)
connecting: set[ClientData] = set()
clients: set[ClientData] = set()
plugins = []
if config.allow_server_actual_version:
    config.allow_client_version = __version__

log_queue = SimpleQueue()
queue_handler = QueueHandler(log_queue)
loghandler = logging.StreamHandler()
loghandler.setFormatter(
    logging.Formatter(
        fmt="[%(asctime)s][%(name)s]: %(message)s",
        datefmt="%H:%M:%S"
    )
)
listener = QueueListener(log_queue, loghandler)
listener.start()

initlogger = logging.getLogger("init")
pluginslogger = logging.getLogger("plugins")
shutdownlogger = logging.getLogger("shutdown")
wslogger = logging.getLogger("ws")
cachelogger = logging.getLogger("cache")

for x in (initlogger, pluginslogger, shutdownlogger, wslogger, cachelogger):
    x.setLevel(config.log_level)
    x.addHandler(queue_handler)

def process_event(etype: str, etrigger: str | None = None, *args, **kwargs):
    for x in plugins:
        for ev in x["obj"].events:
            if ev.etype == etype and ev.etrigger == etrigger:
                if ev.etype in ["on_startup", "on_shutdown"]:
                    try:
                        cb = ev.callback(config, x["logger"])
                        if not cb:
                            pluginslogger.warning(f"Callback returns False in {x['id']}.")
                    except Exception as e:
                        pluginslogger.error(f"Got exception when processing {ev.etype} event in {x['id']} plugin: {e}")
                elif ev.etype == "on_packet":
                    try:
                        cb = ev.callback(config, x["logger"], clients, messages, *args, **kwargs)
                        if not cb:
                            pluginslogger.warning(f"Callback returns False in {x['id']}.")
                    except Exception as e:
                        pluginslogger.error(f"Got exception when processing {ev.etype} event in {x['id']} plugin: {e}")
                else:
                    pluginslogger.warning(f"Can't process event for plugin '{x['name']}', invalid etype - {ev.etype}.")

async def lifespan(app: FastAPI):
    initlogger.info(f"Starting MUCO Server ({__version__}) with config:")
    initlogger.debug(f" - ip: {config.ip}")
    initlogger.debug(f" - port: {config.port}")
    initlogger.debug(f" - server_size: {config.server_size}")
    initlogger.debug(f" - server_message_size: {config.server_message_size}")
    initlogger.debug(f" - server_history_size: {config.server_history_size}")
    initlogger.debug(f" - server_nickname: {config.server_nickname}")
    initlogger.debug(f" - server_path: {config.server_path}")
    initlogger.debug(f" - allow_client_version: {config.allow_client_version}")
    initlogger.debug(f" - tls (certs): {'enabled' if config.certs is not None else 'disabled'}")
    os.makedirs(config.plugins_directory, exist_ok=True)
    os.makedirs(config.errorlog_directory, exist_ok=True)
    os.makedirs(config.cache_directory, exist_ok=True)

    pluginslogger.info("Loading plugins...")
    sys.path.insert(0, config.plugins_directory)
    for plugin in os.listdir(config.plugins_directory):
        plugincfg = os.path.join(config.plugins_directory, plugin, "index.json")
        if os.path.exists(plugincfg):
            with open(plugincfg) as f:
                data = json.load(f)

                id = data.get("id")
                name = data.get("name")
                description = data.get("description")
                version = data.get("version")
                manifest = data.get("manifest")
                if None in [id, name, description, version, manifest]:
                    pluginslogger.error(f"Can't load {plugin}, invalid index.json.")
                else:
                    mainfile = manifest.get("main")
                    entry = manifest.get("entry")
                    if None in [mainfile, entry]:
                        pluginslogger.warning(f"Can't load {plugin}, invalid manifest.")
                    else:
                        try:
                            spec = importlib.util.spec_from_file_location(
                                f"{plugin}.{entry.removesuffix('.py')}",
                                os.path.abspath(os.path.join(config.plugins_directory, plugin, mainfile))
                            )
                            module = importlib.util.module_from_spec(spec)
                            module.__package__ = plugin
                            spec.loader.exec_module(module)
                            pluginobj = getattr(module, entry)

                            pluginlogger = logging.getLogger(f"plugins::{id}")
                            pluginlogger.setLevel(config.log_level)
                            pluginlogger.addHandler(queue_handler)

                            plugins.append({
                                "id" : id,
                                "name" : name,
                                "version" : version,
                                "obj" : pluginobj,
                                "logger" : pluginlogger
                            })
                            pluginslogger.info(f"Loaded '{plugin}' plugin.")
                        except Exception as e:
                            pluginslogger.error(f"Can't load {plugin}, invalid manifest values (wrong entry?): {e}")       
        else:
            pluginslogger.warning(f"Ignoring '{plugin}' (index.json not found).")
    sys.path.pop(0)
    pluginslogger.info("Initializing plugins...")
    process_event("on_startup")

    serverip = socket.gethostbyname(socket.gethostname())
    pluginslogger.info(f"Server link: ws{'s' if config.certs is not None else ''}://{serverip}:{config.port}{config.server_path}")
    initlogger.info("Done! Server started.")
    yield
    shutdownlogger.info("Shutting down MUCO Server...")
    process_event("on_shutdown")

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
    
    shutdownlogger.info("Bye!")

app = FastAPI(
    title="MUCO WebSocket Server",
    version=__version__,
    lifespan=lifespan
)

def process_message(message: Packet):
    bs4 = BeautifulSoup(message["text"], "lxml")
    for tag in bs4.find_all(["img", "video", "audio"]):
        if tag.get("src", "").startswith("data:") and "base64" in tag["src"]:
            rawbase64 = tag["src"].split(";")
            rawdata = base64.b64decode(rawbase64[-1].split(",")[-1])

            fileid = hashlib.sha256(rawdata).hexdigest()
            with open(os.path.join(config.cache_directory, fileid), "wb") as f:
                f.write(rawdata)
            tag["src"] = f"http{'' if config.certs is None else 's'}://{socket.gethostbyname(socket.gethostname())}:{config.port}/cached/{fileid}"
    return str(bs4)

async def broadcast(text: str, author: str, id: int):

    tasks = []
    for x in clients.copy():
        if x.ws.client_state == WebSocketState.DISCONNECTED:
            clients.discard(x)
        else:
            tasks.append(
                x.ws.send_text(
                    Message(
                        x.server_uuid,
                        text,
                        author,
                        id
                    ).wsPacket
                )
            )
    await asyncio.gather(*tasks, return_exceptions=True)

@app.get("/cached/{unique_id}")
async def getCached(unique_id: str):
    cachelogger.debug(f"Got request for cached {unique_id}.")

    isCached = os.path.exists(os.path.join(config.cache_directory, unique_id))
    if not isCached:
        cachelogger.debug(f"Request freezed, file {unique_id} is not ready")
    while not isCached:
        isCached = os.path.exists(os.path.join(config.cache_directory, unique_id))
        await asyncio.sleep(1)
    
    try:
        return FileResponse(
            os.path.join(config.cache_directory, unique_id)
        )
    except Exception as e:
        cachelogger.warning(f"Got exception: {e}")
        Response(status_code=204)

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

    wslogger.debug(f"New connection. Sent connmeta and generated server uuid: {server_uuid}.")

    try:
        while True:
            data = json.loads(await ws.receive_text())
            datatype = data.get("type")
            client_uuid = data.get("uuid")

            data.pop("type")
            data.pop("uuid")
            packet = Packet(datatype, client_uuid, **data)

            if datatype is None:
                await ws.close(1000, "unknown packet type")
                break
            elif client_uuid is None:
                wslogger.debug("No UUID in packet. Rejecting and closing connection.")
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
                if x.ws.client_state == WebSocketState.DISCONNECTED:
                    connecting.discard(x)
                elif x.ws == ws and x.client_uuid == client_uuid:
                    client = x
                    break
            else:
                for x in clients.copy():
                    if x.ws.client_state == WebSocketState.DISCONNECTED:
                        clients.discard(x)
                    elif x.ws == ws and x.client_uuid == client_uuid:
                        client = x
                        break

            if client is None:
                wslogger.debug(f"Unknown client detected. Processing to new client: {client_uuid} / {server_uuid}.")
                client = ClientData(
                    ws,
                    client_uuid,
                    server_uuid
                )
                connecting.add(client)

            await asyncio.to_thread(process_event, "on_packet", packet.type, packet, ws)
            if client in connecting:
                if packet.type == "connmeta":
                    wslogger.debug(f"Got connmeta from {client.client_uuid} client.")
                    
                    for x in clients:
                        if x.nickname == packet["nickname"]:
                            wslogger.debug(f"Client {client.client_uuid} using same nickname as {x.client_uuid}. Rejecting connection.")
                            await ws.send_text(
                                ConnectionReject(
                                    client.server_uuid,
                                    "nickname already taken, change nickname"
                                ).wsPacket
                            )
                            await ws.close()
                            break
                    
                    if packet["version"] == config.allow_client_version:
                        wslogger.debug(f"Client {client.client_uuid} using allowed version. Accepting connection.")
                        await ws.send_text(
                            ConnectionAccept(
                                server_uuid
                            ).wsPacket
                        )
                        connecting.discard(client)

                        client.nickname = packet["nickname"]
                        clients.add(client)
                    else:
                        wslogger.debug(f"Client {client.client_uuid} using wrong version - {packet['version']} ({config.allow_client_version} allowed). Rejecting connection.")
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
                    wslogger.debug(f"Client {client.client_uuid} sent unknown packet type - {packet.type}. Closing connection.")
                    connecting.discard(client)
                    await ws.send_text(
                        ConnectionClose(
                            server_uuid
                        ).wsPacket
                    )
                    await ws.close()
            
            else:
                if packet.type == "getHistory":
                    wslogger.debug(f"Client {client.client_uuid} requested server history.")
                    await ws.send_text(
                        History(
                            server_uuid,
                            list(messages)
                        ).wsPacket
                    )
                elif packet.type == "message":
                    wslogger.debug(f"Client {client.client_uuid} sent a message.")

                    if packet["author"] == config.server_nickname:
                        wslogger.debug(f"Client's ({client.client_uuid}) message rejected for using server nickname - {packet['author']}.")
                        await ws.send_text(
                            Message(
                                client.server_uuid,
                                f"Имя '{config.server_nickname}' является серверным. Его нельзя использовать.",
                                config.server_nickname,
                                int(time.time())
                            ).wsPacket
                        )

                    else:
                        if any([x in packet["text"] for x in ("<audio", "<img", "<video")]):
                            text = await asyncio.to_thread(process_message, packet)
                        else:
                            text = packet["text"]

                        if len(text) > config.server_message_size:
                            wslogger.debug(f"Client's ({client.client_uuid}) message too big - {len(text)}, max allowed is {config.server_message_size}.")
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    f"Сообщение слишком большое (>{config.server_message_size}).",
                                    config.server_nickname,
                                    int(time.time())
                                ).wsPacket
                            )
                        else:
                            wslogger.debug(f"chat / {client.client_uuid}::{client.nickname}: {text}")
                        
                            messages.append(packet.content)
                            if len(messages) > config.server_history_size:
                                messages.pop(0)
                            
                            await broadcast(
                                text,
                                client.nickname,
                                packet["id"]
                            )
                
                elif packet.type == "privateMessage":
                    wslogger.debug(f"Client {client.client_uuid} requested private message ('{packet['author']}'->'{packet['touser']}').")

                    if config.server_nickname == packet['author']:
                        wslogger.debug(f"Client's ({client.client_uuid}) private message rejected for using server nickname.")
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
                            wslogger.debug(f"Client's ({client.client_uuid}) private message can't delivered, touser is unknown client.")
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    f"Пользователь '{packet['touser']}' не найден.",
                                    config.server_nickname,
                                    int(time.time())
                                ).wsPacket
                            )
                        else:
                            wslogger.debug(f"privateChat / {client.client_uuid}::{client.nickname}->{touser.nickname}: {packet['text']}")
                            await ws.send_text(
                                Message(
                                    client.server_uuid,
                                    packet["text"],
                                    f"{touser.nickname}<=",
                                    int(time.time())
                                ).wsPacket
                            )
                            await touser.ws.send_text(
                                Message(
                                    client.server_uuid,
                                    packet["text"],
                                    f"{client.nickname}=>",
                                    int(time.time())
                                ).wsPacket
                            )
                
                elif packet.type == "disconnect":
                    wslogger.debug(f"Client {client.client_uuid} disconnected.")
                    clients.discard(client)
                    await ws.send_text(
                        DisconnectionAgree(
                            client.server_uuid
                        ).wsPacket
                    )
                    await ws.close()
                    break

                elif packet.type == "nickchange":
                    wslogger.debug(f"Client {client.client_uuid} requested nickname change ({client.nickname}->{packet['nickname']}).")

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
        wslogger.debug("Websocket disconnected, discarding client.")
        for client in clients.copy():
            if ws == client.ws:
                clients.discard(client)
                break

    except Exception as e:
        wslogger.debug(f"Got exception: {e}")
        async with asyncopen(os.path.join(config.errorlog_directory, f"exception-{int(time.time())}.log"), "w") as f:
            await f.write(f"Error log on {datetime.now().strftime('%d-%m-%y at %H:%M:%S')}.\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    from uvicorn import Server, Config

    if config.certs is None:
        cfg = Config(
            app,
                config.ip,
                config.port,
                workers=1,
                access_log=False
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