import gc
import network
import time

from conf import settings


W_INTERFACE = network.WLAN(network.STA_IF)


def connect(retries=None):
    """
    Starts the WLAN interface and makes a connection.

    """
    STAT_MAP = {
        network.STAT_IDLE: "Not currently connected",
        network.STAT_CONNECTING: "Connecting",
        network.STAT_WRONG_PASSWORD: "Incorrect password",
        network.STAT_NO_AP_FOUND: "No access point found",
        network.STAT_ASSOC_FAIL: "Connection failed",
        network.STAT_HANDSHAKE_TIMEOUT: "Connection failed",
        network.STAT_BEACON_TIMEOUT: "Connection failed",
        network.STAT_GOT_IP: "Connection successful",
    }
    W_INTERFACE.active(True)
    # Only make a few attempts to connect
    W_INTERFACE.config(reconnects=retries or 3)
    W_INTERFACE.connect(settings.WIFI_SSID, settings.WIFI_PASSWORD)
    print("Connecting to WiFi...", end="")
    while W_INTERFACE.status() == network.STAT_CONNECTING:
        time.sleep(1)
        print(".", end="")

    status = W_INTERFACE.status()
    print(STAT_MAP.get(status, "Unknown error: {}".format(status)))

    if status != network.STAT_GOT_IP or not W_INTERFACE.isconnected():
        W_INTERFACE.disconnect()
        W_INTERFACE.active(False)

    gc.collect()


# TODO: tests, handle disconnects, reconnect etc
