from core import ConnectionReject, DisconnectionAgree, Packet, Message, History, ConnectionAccept, ConnectionMeta

import json, time
from dataclasses import dataclass

from aiohttp import web
import aiohttp

__version__ = "0.1.32"

@dataclass
class ServerConfig:
    ip: str = "0.0.0.0"
    port: int = 5656
    server_size: int = 256
    server_message_size: int = 8192
    server_history_size: int = 1024
    server_path: str = "/"
    certs: tuple | None = None
    allow_client_version: str = __version__

class MUCOServer:

    def __init__(
            self,
            config: ServerConfig
    ):
        self.config = config
        self.address = (config.ip, config.port)
        self.app = web.Application()
        self.app.router.add_get(config.server_path, self._handler)

        self.history = []
        self.connecting = set()
        self.clients = set()

    async def _broadcast(self, packet: Packet):
        for ws in self.clients.copy():
            if ws.closed:
                self.clients.discard(ws)
            else:
                await ws.send_str(packet.wsPacket)
    
    async def _unknownClient(self, ws):

        if ws not in self.connecting:
            await ws.send_str(
                ConnectionMeta(self.config.allow_client_version).wsPacket
            )
            self.connecting.add(ws)
        
        async for msg in ws:
            
            print(msg, msg.data)
            data = json.loads(msg.data)
            type = data["type"]
            data.pop("type")
            packet = Packet(type, **data)

            if packet.type == "connmeta":
                if packet["version"] == self.config.allow_client_version:
                    await ws.send_str(
                        ConnectionAccept().wsPacket
                    )
                    self.clients.add(ws)
                else:
                    await ws.send_str(
                        ConnectionReject(f"version mismatch: client is {packet['version']}, server is {self.config.allow_client_version}").wsPacket
                    )
                self.connecting.discard(ws)
            
            return ws

    async def _handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:

            if ws not in self.clients:
                await self._unknownClient(ws)

            async for msg in ws:

                if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):

                    data = json.loads(msg.data)
                    type = data["type"]
                    data.pop("type")
                    packet = Packet(type, **data)

                    if packet.type == "message":
                        if len(packet['text']) > self.config.server_message_size:
                            await ws.send_str(
                                Message(
                                    f"Сообщение слишком длинное (>{self.config.server_message_size})",
                                    "server",
                                    int(time.time())
                                ).wsPacket
                            )
                        else:
                            print(f"[msg::{packet['id']}]| {packet['author']}: {packet['text']}")
                            self.history.append(packet.content)
                            await self._broadcast(
                                Message(
                                    packet["text"],
                                    packet["author"],
                                    packet["id"]
                                )
                            )
                    
                    elif packet.type == "getHistory":
                        await ws.send_str(
                            History(
                                self.history
                            ).wsPacket
                        )
                    
                    elif packet.type == "disconnect":
                        await ws.send_str(
                            DisconnectionAgree().wsPacket
                        )
                        self.clients.remove(ws)
                        await ws.close()
                        break
                
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    self.clients.discard(ws)
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.clients.discard(ws)
                    await ws.close()
                
                elif msg.type == aiohttp.WSMsgType.PING:
                    await ws.pong()
                
            return ws
        
        except Exception as e:
            print("-=-=-=-=-=-=-")
            print(f"Got Exception: {e}")
            print(f"WebSocket: {ws}")
    
    def run(self):
        print(f"Starting MUCO server on {self.config.ip}:{self.config.port}.")
        print(f"Server path: {self.config.server_path}")
        print(f"Server size: {self.config.server_size}")
        print(f"History size: {self.config.server_history_size}")
        
        ssl_context = None
        if self.config.certs:
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(*self.config.certs)
        
        web.run_app(
            self.app,
            host=self.config.ip,
            port=self.config.port,
            ssl_context=ssl_context
        )

if __name__ == "__main__":
    server = MUCOServer(
        ServerConfig()
    )
    server.run()