import re
import socket
import time
from collections import namedtuple

from conf import settings


PING_RE = re.compile("^PING\ :(\w+\.twitch\.tv)")
# 1: Username
# 2: Action/Command
# 3: Channel
METADATA_PARSER = re.compile("^([0-9a-zA-Z\_]+)![0-9a-zA-Z\_]+@[0-9a-zA-Z\_]+\.[0-9a-zA-Z]+\.twitch\.tv\ ([0-9a-zA-Z\_]+)\ ([\#0-9a-zA-Z_]+)$")


def to_bytes(val):
    if isinstance(val, bytes):
        return val
    return val.encode("utf-8")


def from_bytes(val):
    if isinstance(val, str):
        return val
    return val.decode()


BaseMessage = namedtuple("Message", ["tags_str", "username", "action", "channel", "content"])


class Message(BaseMessage):
    @classmethod
    def from_text(cls, data):
        """
        Given a Twitch IRC message text including tags, parse
        the message and return a BaseMessage tuple.

        Each message has three disctinct parts:
            1. tags https://dev.twitch.tv/docs/irc/tags
            2. metadata - username, action/command, channel
            3. content - the actual content of the message such as the text someone entered

        """
        try:
            tags_str, metadata_str, content = [p.strip() for p in data.split(":")]
        except ValueError:
            return None


        metadata = METADATA_PARSER.match(metadata_str)

        if metadata is not None:
            return cls(
                tags_str,
                metadata.group(1),
                metadata.group(2),
                metadata.group(3),
                content,
            )
        return None

    def _parse_tags(self):
        """
        Lazy parsing for tags.

        """
        tokens = self.tags_str[1:].split(";")
        self._tags = {
            k.strip(): v
            for token in tokens
            for k, v in [token.split("=")]
        }

    @property
    def tags(self):
        """
        Tags exist as a string on the object until this property is
        accessed when the tags will be parsed.

        This will return a dictionary of tags for the message.

        """
        if not hasattr(self, "_tags"):
            self._parse_tags()
        return self._tags


class Client:
    """
    Handles a connection to a Twitch IRC channel as well as callbacks for events.

    """
    def __init__(self, password, nick, channel, addr=None):
        self.addr = addr.split(":") if addr is not None else ("irc.twitch.tv", 6667)
        self.password = password
        self.nick = nick
        self.channel = "#{}".format(channel) if not channel.startswith("#") else channel
        self.sock = None
        self.is_connected = False
        self._registry = dict()

    def connect(self):
        """
        Connects to the IRC server and joins the given channel.
        This also will request tags in messages.

        """
        self.sock = socket.socket()
        self.sock.connect(self.addr)
        self.send("PASS {}".format(self.password))
        self.send("NICK {}".format(self.nick))
        self.send("JOIN {}".format(self.channel))
        self.send("CAP REQ :twitch.tv/tags")
        self.is_connected = True
        # TODO: error handling

    def _listen(self):
        """
        Main listen loop.

        First ensures the client is connected. Following that it will
        receive messages every second and call the handler function.

        """
        if not self.is_connected:
            self.connect()

        while True:
            data = self.recv()
            ping = PING_RE.match(data)
            if ping:
                self.handle_ping(ping.group(1))
            else:
                result = self.handle_message(data)

            if result:
                print(result)

            time.sleep(1)

    def listen(self):
        """
        Wrapper function to cleanly handle interrupts from the
        listen loop.

        """
        try:
            self._listen()
        except KeyboardInterrupt:
            self.sock.close()
            self.is_connected = False

    def recv(self):
        """
        Receive messages from the server and convert to string.

        """
        return from_bytes(self.sock.recv(512))

    def send(self, val, end="\n"):
        """
        Send message to the server, handling line ending and conversion to bytestring.

        """
        self.sock.send(to_bytes("{val}{end}".format(val=val, end=end)))

    def handle_ping(self, host):
        """
        Called when Twitch IRC sends a PING message and responds with PONG.

        See: https://dev.twitch.tv/docs/irc/guide#connecting-to-twitch-irc

        """
        self.send("PONG :{}".format(host))

    def handle_message(self, data):
        """
        Currently not final. Debugs message parsing.

        """
        message = Message.from_text(data)
        if message is not None:
            print(message.username, message.action, message.channel, message.content)
            self._callback("message", message)  # TODO: add additional callbacks

    def register_handler(self, event, fn, unique=False):
        """
        Accepts an event and function and registers that function as
        an event handler to be called.

        If unique is set to true then all other handlers will be removed.

        """
        if event not in self._registry or unique:
            self._registry[event] = [fn]
        else:
            self._registry[event].append(fn)
        return fn

    def on_message(self, fn, unique=False):
        return self.register_handler("message", fn, unique=unique)

    def _callback(self, event, message):
        # TODO: error handling
        for fn in self._registry.get(event, []):
            fn(message)


# Client for testing things, remove me later
#client = Client(settings.TWITCH_IRC_TOKEN, settings.TWITCH_NICK, settings.TWITCH_CHANNEL)
#client.connect()
