import asyncio
import os
import threading
import time
from mitmproxy import options
from mitmproxy.master import Master
from mitmproxy.addons import default_addons

# HTTP/1.1 connection-specific headers that must NOT be forwarded in HTTP/2
_CONNECTION_HEADERS = {
    "connection", "keep-alive", "proxy-connection",
    "transfer-encoding", "upgrade", "te",
}


class ConnectionHeaderCleaner:
    """Strip HTTP/1.1 connection-specific headers that break HTTP/2."""
    def requestheaders(self, flow):
        headers = flow.request.headers
        removed = []
        for key in list(headers.keys()):
            if key.lower() in _CONNECTION_HEADERS:
                removed.append(key)
                del headers[key]
        if removed and flow.request.http_version == "HTTP/2.0":
            from mitmproxy import ctx
            ctx.log.debug(f"Stripped HTTP/2-incompatible headers: {removed}")


class ProxyInstance:
    def __init__(self, name, port, listen_host, upstream, addon_script_path,
                 proxy_settings=None, log_callback=None):
        self.name = name
        self.port = port
        self.listen_host = listen_host
        self.upstream = upstream
        self.addon_script_path = addon_script_path
        self.proxy_settings = proxy_settings or {}
        self.log_callback = log_callback
        self.master = None
        self.thread = None
        self.loop = None
        self._running = False

    @property
    def is_running(self):
        return self._running and self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.is_running:
            return False, f"{self.name} 已在运行中"
        self._running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        time.sleep(0.5)
        return True, f"{self.name} 已启动 ({self.listen_host}:{self.port})"

    def stop(self):
        if not self.is_running:
            return False, f"{self.name} 未在运行"
        self._running = False
        try:
            if self.master:
                self.master.shutdown()
        except Exception:
            pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        return True, f"{self.name} 已停止"

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        s = self.proxy_settings
        opts = options.Options(
            listen_host=self.listen_host,
            listen_port=self.port,
            ssl_insecure=s.get("ssl_insecure", True),
            http2=s.get("http2", True),
        )
        if self.upstream:
            opts.update(mode=[f"upstream:{self.upstream}"])

        # Optional: upstream cert
        if s.get("ssl_verify_upstream_trusted_ca"):
            opts.update(
                ssl_verify_upstream_trusted_ca=s["ssl_verify_upstream_trusted_ca"]
            )

        async def run_proxy():
            self.master = Master(opts)
            self.master.addons.add(*default_addons())
            self.master.addons.add(ConnectionHeaderCleaner())
            if self.log_callback:
                self.master.addons.add(LogAddon(self.name, self.log_callback))
            if self.addon_script_path:
                try:
                    self.master.addons.add(ScriptAddon(self.addon_script_path))
                except Exception:
                    pass
            await self.master.run()

        try:
            self.loop.run_until_complete(run_proxy())
        except Exception:
            pass
        finally:
            try:
                self.loop.close()
            except Exception:
                pass


class LogAddon:
    """Logs lifecycle and errors. Suppresses noise from connection-level errors."""
    def __init__(self, proxy_name, callback):
        self.proxy_name = proxy_name
        self.callback = callback

    def running(self):
        self.callback(f"[{self.proxy_name}] 代理已启动")

    def done(self):
        self.callback(f"[{self.proxy_name}] 代理已关闭")

    def error(self, flow):
        msg = str(flow.error)
        # Suppress noisy HTTP/2 connection-level errors
        if "Connection-specific header field" in msg:
            return
        if "HTTP/2 protocol error" in msg:
            return
        self.callback(f"[{self.proxy_name}] 错误: {flow.error}")


class ScriptAddon:
    """Loads the generated addon module and auto-reloads when the file changes."""
    def __init__(self, script_path):
        self.script_path = script_path
        self.module = None
        self._mtime = 0
        self._load()

    def _load(self):
        import importlib.util
        try:
            self._mtime = os.path.getmtime(self.script_path)
            spec = importlib.util.spec_from_file_location("generated_addon", self.script_path)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        except Exception:
            self.module = None

    def _maybe_reload(self):
        try:
            current_mtime = os.path.getmtime(self.script_path)
            if current_mtime != self._mtime:
                self._load()
        except OSError:
            pass

    def request(self, flow):
        self._maybe_reload()
        if self.module:
            for addon in getattr(self.module, "addons", []):
                if hasattr(addon, "request"):
                    addon.request(flow)

    def response(self, flow):
        self._maybe_reload()
        if self.module:
            for addon in getattr(self.module, "addons", []):
                if hasattr(addon, "response"):
                    addon.response(flow)

    def error(self, flow):
        self._maybe_reload()
        if self.module:
            for addon in getattr(self.module, "addons", []):
                if hasattr(addon, "error"):
                    addon.error(flow)


class ProxyManager:
    def __init__(self, generated_dir):
        self.generated_dir = generated_dir
        self.proxy1 = None
        self.proxy2 = None

    def start_proxy1(self, port, listen_host, upstream, rules, scripts_dir,
                     proxy_settings=None, log_callback=None):
        addon_path = os.path.join(self.generated_dir, "addon_proxy1.py")
        from .addon_generator import generate_addon_script
        generate_addon_script(rules, "proxy1", scripts_dir, addon_path)
        self.proxy1 = ProxyInstance("Proxy1", port, listen_host, upstream,
                                    addon_path, proxy_settings, log_callback)
        return self.proxy1.start()

    def start_proxy2(self, port, listen_host, upstream, rules, scripts_dir,
                     proxy_settings=None, log_callback=None):
        addon_path = os.path.join(self.generated_dir, "addon_proxy2.py")
        from .addon_generator import generate_addon_script
        generate_addon_script(rules, "proxy2", scripts_dir, addon_path)
        self.proxy2 = ProxyInstance("Proxy2", port, listen_host, upstream,
                                    addon_path, proxy_settings, log_callback)
        return self.proxy2.start()

    def stop_proxy1(self):
        if self.proxy1:
            return self.proxy1.stop()
        return False, "Proxy1 未初始化"

    def stop_proxy2(self):
        if self.proxy2:
            return self.proxy2.stop()
        return False, "Proxy2 未初始化"

    def stop_all(self):
        r1 = self.stop_proxy1()
        r2 = self.stop_proxy2()
        return r1, r2

    @property
    def proxy1_running(self):
        return self.proxy1 is not None and self.proxy1.is_running

    @property
    def proxy2_running(self):
        return self.proxy2 is not None and self.proxy2.is_running
