
import json

class Packet:
    
    def __init__(
            self,
            type: str,
            **content
    ):
        self.type = type
        self.content = content

    def __setitem__(self, key, item):
        self.content[key] = item
    
    def __getitem__(self, key):
        return self.content[key]
    
    @property
    def wsJSON(self): return {"type": self.type, **self.content}

    @property
    def wsPacket(self): return json.dumps({"type": self.type, **self.content})

class ConnectionMeta(Packet):

    def __init__(self, version: str):
        super().__init__("connmeta", **{"version": version})

class ConnectionAccept(Packet):

    def __init__(self):
        super().__init__("connaccept")

class ConnectionReject(Packet):

    def __init__(self, error: str):
        super().__init__("connreject", **{"error": error})

class ConnectionClose(Packet):

    def __init__(self):
        super().__init__("connclose")

class DisconnectionAgree(Packet):

    def __init__(self):
        super().__init__("dcon-agree")

class GetHistory(Packet):

    def __init__(self, lastmsg: int = 512):
        super().__init__("getHistory", **{"from": lastmsg})

class History(Packet):

    def __init__(self, messages: list):
        super().__init__("history", **{"messages": messages})

class Message(Packet):

    def __init__(self, text: str, author: str, id: int):
        super().__init__("message", **{"text": text, "author": author, "id": id})