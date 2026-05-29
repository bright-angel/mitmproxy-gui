import json
import os

DEFAULT_CONFIG = {
    "proxy1": {
        "listen_port": 8081,
        "listen_host": "127.0.0.1",
        "upstream": "127.0.0.1:8080"
    },
    "proxy2": {
        "listen_port": 8082,
        "listen_host": "127.0.0.1",
        "upstream": ""
    },
    "settings": {
        "ssl_insecure": True,
        "http2": True,
        "ssl_verify_upstream_trusted_ca": ""
    }
}


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_proxy1_config(self):
        return self.config.get("proxy1", DEFAULT_CONFIG["proxy1"])

    def get_proxy2_config(self):
        return self.config.get("proxy2", DEFAULT_CONFIG["proxy2"])

    def get_settings(self):
        return self.config.get("settings", DEFAULT_CONFIG["settings"])

    def set_proxy_config(self, proxy_key, listen_port, listen_host, upstream):
        self.config[proxy_key] = {
            "listen_port": int(listen_port),
            "listen_host": listen_host,
            "upstream": upstream
        }
        self.save()

    def set_settings(self, settings_dict):
        self.config["settings"] = settings_dict
        self.save()
