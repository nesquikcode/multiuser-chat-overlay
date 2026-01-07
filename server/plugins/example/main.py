from .sdk import ClientData, Packet, ServerPlugin, WebSocket

from pydantic import BaseModel
from logging import Logger
import logging

import json, os

global cfg
cfg = {}

plugin = ServerPlugin()

@plugin.event("on_startup", None)
def startup(config: BaseModel, logger: Logger):
    global cfg

    with open(os.path.join(os.path.dirname(__file__), "index.json")) as f:
        pluginconfig = json.load(f)
    logger.info(f"'{pluginconfig.get('name')}' startup...")
    logger.info(f"Plugin config: {pluginconfig}")
    logger.info(f"Server config: {config.model_dump()}")
    cfg = pluginconfig
    return True

@plugin.event("on_packet", "message")
def onMessage(config: BaseModel, logger: Logger, clients: set[ClientData], messages: list, packet: Packet, ws: WebSocket):
    return True

@plugin.event("on_shutdown", None)
def shutdown(config: BaseModel, logger: Logger):
    logger.info("Shutting down...")
    return True