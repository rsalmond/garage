import os
import time
import hashlib
import logging
import asyncio
import collections

from common.messages import Messages

from websockets.exceptions import ConnectionClosedOK
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status

CLIENT_KEY = "12345"

log = logging.getLogger("uvicorn")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log.handlers[0].setFormatter(formatter)
log.setLevel(logging.DEBUG)

queue = collections.deque(maxlen=25)

app = FastAPI()
BUFFER = []


@app.get("/webhook")
async def webhook():
    log.info("Adding message to queue")
    queue.appendleft(Messages.REQ_DOOR_STATUS)


def is_authorized(payload):
    pass


class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.pending_disconnections = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        log.debug(f"Accepting connection: {shortname(ws)}")
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        log.debug(f"Disconnecting: {shortname(ws)}")
        self.active_connections.remove(ws)
        print([shortname(x) for x in self.active_connections])

    def mark_for_disconnection(self, ws: WebSocket):
        self.pending_disconnections.append(ws)

    def purge_pending_disconnections(self):
        log.debug("Purging pending disconnections.")
        for ws in self.pending_disconnections:
            self.disconnect(ws)

        self.pending_disconnections = []

    async def broadcast(self, payload: dict):
        log.debug(f"Iterating over {len(self.active_connections)} connections.")

        for ws in self.active_connections:
            log.debug(f"Sending payload {payload} to {shortname(ws)}.")
            try:
                await ws.send_json(payload)
            except (WebSocketDisconnect, ConnectionClosedOK) as e:
                log.debug(f"client {shortname(ws)} disconnected with {e}")
                self.mark_for_disconnection(ws)
                continue

        self.purge_pending_disconnections()


manager = ConnectionManager()


def shortname(name):
    hashed = hashlib.sha256()
    hashed.update(str(name).encode("utf-8"))
    return hashed.hexdigest()[:6]


@app.websocket("/ws")
async def websocket_handler(ws: WebSocket):

    await manager.connect(ws)

    client_key = ws.headers.get("client_key")

    if client_key is None:
        log.info("Closing websocket connection due to missing client key.")
        await ws.close()
        return
    else:
        if client_key != CLIENT_KEY:
            log.info("Closing websocket connection due to invalid client key.")
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    while True:
        try:
            # log.debug(f"Len queue: {len(queue)}, Num Conns: {len(manager.active_connections)}")
            if len(queue) > 0:
                payload = queue.pop()
                await manager.broadcast(payload)

            await asyncio.sleep(0.2)

        except Exception as e:
            fuck = e
            breakpoint()
