import gc
import json


class Settings:
    """
    Simple settings wrapper that will load settings from
    a configuration file.

    The file is lazy loaded the first time a setting is
    accessed.

    """
    defaults = {
        "WIFI_SSID": "",
        "WIFI_PASSWORD": "",
        "TWITCH_IRC_TOKEN": "",
        "TWITCH_NICK": "",
        "TWITCH_PREFIX": "",
        "TWITCH_CHANNEL": "",
    }
    _settings = None

    def __init__(self, config=None):
        self.config_file = config or "config.json"

    def __getattr__(self, attr_name):
        if self._settings is None:
            self._load_config()

        return self._settings[attr_name]


    def _load_config(self):
        with open(self.config_file) as fp:
            data = json.load(fp)

        self._settings = {
            key: data.get(key, default)
            for key, default in self.defaults.items()
        }

        gc.collect()


settings = Settings()


# TODO: Tests =/
