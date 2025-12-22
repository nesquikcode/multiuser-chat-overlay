from core import DisconnectionAgree, Packet, Message, History, ConnectionAccept

import json
from dataclasses import dataclass

from aiohttp import web
import aiohttp

@dataclass
class ServerConfig:
    ip: str = "0.0.0.0"
    port: int = 5656
    server_size: int = 256
    server_history_size: int = 1024
    server_path: str = "/"
    certs: tuple | None = None

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
        self.clients = set()

    async def _broadcast(self, packet: Packet):
        for ws in self.clients.copy():
            await ws.send_str(packet.wsPacket)
    
    async def _unknownClient(self, ws):
        self.clients.add(ws)
        await ws.send_str(
            ConnectionAccept().wsPacket
        )

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
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
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