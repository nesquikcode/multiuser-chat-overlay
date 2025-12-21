#!/usr/bin/env python

"""Echo server using the asyncio API."""

import asyncio
from http import client
from websockets.asyncio.server import serve
import random, json
import ssl

size = 512

global messages
messages = []
clients = set()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

async def muco(websocket):
    global messages
    try:
        await websocket.send(json.dumps({
            "type" : "connaccept",
            "ip" : websocket.local_address[0],
            "port" : websocket.local_address[1]
        }))
        clients.add(websocket)

        async for message in websocket:
            content = json.loads(message)
            if content["type"] == "getHistory":
                await websocket.send(json.dumps({
                    "type" : "history",
                    "messages" : messages
                }))
            elif content["type"] == "message":
                messages.append({
                    "text" : content["text"],
                    "author" : content["author"],
                    "id" : content["id"]
                })
                if len(messages) > size:
                    messages = messages[:size]
                await broadcast(json.dumps({
                    "type" : "message",
                    "text" : content["text"],
                    "author" : content["author"],
                    "id" : content["id"]
                }))
    except Exception as e:
        print(e)
        if websocket in clients:
            clients.remove(websocket)

async def broadcast(msg):
    for x in clients.copy():
        try: await x.send(msg)
        except:
            clients.remove(x)  

async def main():
    async with serve(muco, "0.0.0.0", 5656, ssl=ssl_context) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())