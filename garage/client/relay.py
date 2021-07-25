import os
import time
import logging

from pylibftdi import Driver, BitBangDevice, FtdiError

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
log = logging.getLogger()

relay_address = {
    1: "2",
    2: "8",
    3: "20",
    4: "80",
    5: "1",
    6: "4",
    7: "10",
    8: "40",
    "all": "FF",
}

OR = 1
AND = 2
RELAY = "DAE001l0"


class Relay:

    _device = None

    def __init__(self):
        self._get_relay()

    def _write(self, value, operation):
        try:
            if operation == OR:
                self._device.port |= value
            elif operation == AND:
                self._device.port &= value
        except FtdiError as e:
            log.error("Lost USB connection, trying to recover.")
            del self._device
            self._get_relay()
            self.all_off()

    def all_on(self):
        self._write(int(relay_address.get("all"), 16), OR)

    def all_off(self):
        self._write(~int(relay_address.get("all"), 16), AND)

    def on(self, relay_id):
        self._write(int(relay_address.get(relay_id), 16), OR)

    def off(self, relay_id):
        self._write(~int(relay_address.get(relay_id), 16), AND)

    def _get_relay(self):
        log.info("Scanning for relay devices.")
        for device in Driver().list_devices():
            vendor, product, serial = device
            if serial == RELAY:
                log.info("Relay device found.")
                self._device = BitBangDevice(serial)
                break

        if self._device is None:
            raise Exception("Could not initialize relay device.")
