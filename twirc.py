import re
import socket
import time

from conf import settings


PING_RE = re.compile(r"^PING\s:(\w+\.twitch\.tv)")
PARSER_RE = re.compile(r"^:\w+!\w+@\w+\.\w+\.twitch\.tv\s(?P<type>\w+)\s(?P<channel>[\#\w]+)\s:(?P<message>.*)(?:\n|$)")


def to_bytes(val):
    return val.encode("utf-8")


def from_bytes(val):
    return val.decode()


class IRCClient:
    """
    Handles a connection to a Twitch IRC channel

    """
    def __init__(self, password, nick, channel, addr=None):
        self.addr = addr.split(":") if addr is not None else ("irc.twitch.tv", 6667)
        self.password = password
        self.nick = nick
        self.channel = "#{}".format(channel) if not channel.startswith("#") else channel
        self.sock = None
        self.is_connected = False

    def connect(self):
        self.sock = socket.socket()
        self.sock.connect(self.addr)
        self.send("PASS {}".format(self.password))
        self.send("NICK {}".format(self.nick))
        self.send("JOIN {}".format(self.channel))
        self.is_connected = True
        # TODO: error handling

    def listen(self):
        if not self.is_connected:
            self.connect()

        while True:
            data = self.recv()
            ping = PING_RE.match(data)
            if ping:
                self.handle_ping(ping.group(1))
            print(data)
            time.sleep(1)

    def recv(self):
        return from_bytes(self.sock.recv(512))

    def send(self, val, end="\n"):
        self.sock.send(to_bytes("{val}{end}".format(val=val, end=end)))

    def handle_ping(self, host):
        self.send("PING :{}".format(host))


# Client for testing things, remove me later
client = IRCClient(settings.TWITCH_IRC_TOKEN, settings.TWITCH_NICK, settings.TWITCH_CHANNEL)
#client.connect()
