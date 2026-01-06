
from typing import Callable, Literal
from pydantic import BaseModel
from logging import Logger
from fastapi.websockets import WebSocket

import json

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

class ServerEvent:

    def __init__(
            self,
            callback: Callable[[BaseModel, Logger], bool] | Callable[[BaseModel, Logger, Packet, WebSocket], bool],
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