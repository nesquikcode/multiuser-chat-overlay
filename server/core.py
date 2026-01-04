
import json
from fastapi import WebSocket

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