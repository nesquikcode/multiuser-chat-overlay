
from typing import Callable, Literal
from pydantic import BaseModel
from logging import Logger
from fastapi.websockets import WebSocket

import logging
import json
import os

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

class ClientData:

    def __init__(
            self,
            websocket: WebSocket,
            uuid: str,
            server_uuid: str,
            nickname: str | None = None
    ):
        self.ws = websocket
        self.server_uuid = server_uuid
        self.client_uuid = uuid
        self.nickname = nickname

class Packet:
    
    def __init__(
            self,
            type: str,
            uuid: str,
            **content
    ):
        self.type = type
        self.uuid = uuid
        self.content = content

    def __setitem__(self, key, item):
        self.content[key] = item
    
    def __getitem__(self, key):
        return self.content[key]
    
    @property
    def wsJSON(self): return {"type": self.type, "uuid": self.uuid, **self.content}

    @property
    def wsPacket(self): return json.dumps({"type": self.type, "uuid": self.uuid, **self.content})

class ConnectionMeta(Packet):

    def __init__(self, uuid: str, version: str, nickname: str):
        super().__init__("connmeta", uuid, **{"version": version, "nickname": nickname})

class ConnectionAccept(Packet):

    def __init__(self, uuid: str):
        super().__init__("connaccept", uuid)

class ConnectionReject(Packet):

    def __init__(self, uuid: str, error: str):
        super().__init__("connreject", uuid, **{"error": error})

class ConnectionClose(Packet):

    def __init__(self, uuid: str):
        super().__init__("connclose", uuid)

class Disconnect(Packet):

    def __init__(self, uuid: str):
        super().__init__("disconnect", uuid)

class DisconnectionAgree(Packet):

    def __init__(self, uuid: str):
        super().__init__("dcon-agree", uuid)

class GetHistory(Packet):

    def __init__(self, uuid: str, lastmsg: int = 512):
        super().__init__("getHistory", uuid, **{"from": lastmsg})

class History(Packet):

    def __init__(self, uuid: str, messages: list):
        super().__init__("history", uuid, **{"messages": messages})

class Message(Packet):

    def __init__(self, uuid: str, text: str, author: str, id: int):
        super().__init__("message", uuid, **{"text": text, "author": author, "id": id})

class NicknameChange(Packet):

    def __init__(self, uuid: str, nickname: str):
        super().__init__("nickchange", uuid, **{"nickname": nickname})

class ServerEvent:

    def __init__(
            self,
            callback: Callable[[BaseModel, Logger], bool] | Callable[[BaseModel, Logger, Packet, WebSocket, set[ClientData]], bool],
            event_type: Literal['on_startup', 'on_packet', 'on_shutdown'],
            event_trigger: Literal['connmeta', 'connaccept', 'connreject', 'connclose', 'message', 'privateMessage', 'getHistory', 'history', 'nickchange'] | None = None
        ):
            self.callback = callback
            self.event_type = event_type
            self.event_trigger = event_trigger if event_type == "on_packet" else None
    
    @property
    def etype(self): return self.event_type

    @property
    def etrigger(self): return self.event_trigger

class ServerPlugin:

    def __init__(
            self,
            events: list[ServerEvent] = []
    ):
        self.events = events
    
    def add_event(self, event: ServerEvent):
        self.events.append(event)
    
    def event(self, etype, etrigger):
        def wrapper(func):
            self.events.append(
                ServerEvent(
                    func,
                    etype,
                    etrigger
                )
            )
            return func
        return wrapper