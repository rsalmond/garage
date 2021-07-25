import os
import json
import time
import logging
import websocket

from relay import Relay

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
log = logging.getLogger()


class DoorClient:
    def __init__(self):
        self._configure()
        log.debug("Initializing garage door device.")
        self._garage_door = Relay()
        log.debug("Garage door device initialized.")

    def _configure(self):

        self.server = os.environ.get("DOOR_SERVER_URI")
        if self.server is None:
            raise Exception("No server URI specified!")

        self.client_key = os.environ.get("DOOR_CLIENT_KEY")
        if self.client_key is None:
            raise Exception("No client key specified!")

    def on_message(self, ws_app, message):
        log.info(f"Received message: {message}")
        self._activate_door()

    def on_error(self, ws_app, error):
        log.error(error)

    def on_close(self, ws_app, close_status, close_msg):
        log.info(f"Closed: {close_status}, {close_msg}")

    def run(self):
        initial_payload = self._make_payload({"client_key": self.client_key})
        self._wsa = websocket.WebSocketApp(
            self.server,
            header=initial_payload,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self._wsa.run_forever(ping_interval=10, ping_timeout=5)

    def get_door_status(self):
        return self._make_payload({"sensor_status": "opened"})

    def _make_payload(self, payload):
        # converted to string because websocket headers shit themselves
        # otherwise
        payload["created"] = str(int(time.time()))
        return payload

    def _activate_door(self):
        self._garage_door.all_on()
        time.sleep(0.2)
        self._garage_door.all_off()

if __name__ == "__main__":
    DoorClient().run()
