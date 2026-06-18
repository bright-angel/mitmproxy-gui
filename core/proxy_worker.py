"""Proxy worker process — runs a single mitmproxy Master in isolation.

This avoids the ctx.master module-level global conflict that prevents
two mitmproxy Masters from coexisting in a single Python process.
Each proxy runs in its own multiprocessing.Process.
"""

import asyncio
import logging
import os
import traceback

from mitmproxy import options
from mitmproxy.master import Master
from mitmproxy.addons import default_addons

# HTTP/1.1 connection-specific headers that must NOT be forwarded in HTTP/2
_CONNECTION_HEADERS = {
    "connection", "keep-alive", "proxy-connection",
    "transfer-encoding", "upgrade", "te",
}

# mitmproxy internal log prefixes to suppress
_NOISY_PREFIXES = (
    "server connection", "server connect", "server disconnect",
    "client connection", "client connect", "client disconnect",
    "TCP", "UDP", "websocket",
    "HTTP/2 connection", "HTTP/2 stream",
    "ALPN", "TLS handshake", "TLS Error:",
    "Unhandled error in task",
    "Traceback (most recent call last)",
    "HTTP(S) proxy",
)


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


class QueueLogHandler(logging.Handler):
    """Send Python logging records to the main process via Queue."""

    def __init__(self, proxy_label, log_queue):
        super().__init__()
        self.proxy_label = proxy_label
        self.log_queue = log_queue
        self.setLevel(logging.DEBUG)

    def emit(self, record):
        level = record.levelname.lower()
        msg = self.format(record)

        if level == "debug":
            return
        if msg:
            low = msg.lower()
            if low.startswith(_NOISY_PREFIXES):
                return

        self.log_queue.put((level, f"[{self.proxy_label}] {msg}"))


class QueueProxyLogAddon:
    """mitmproxy addon for lifecycle events and ctx.log from scripts.

    ctx.log in mitmproxy dispatches through the addon 'log' event,
    NOT through Python's logging module. Both mechanisms are needed:
    - QueueLogHandler captures Python logging (mitmproxy internals)
    - QueueProxyLogAddon.log() captures ctx.log from addon scripts
    """

    def __init__(self, proxy_label, log_queue, ready_event):
        self.proxy_label = proxy_label
        self.log_queue = log_queue
        self._ready_event = ready_event
        self._hook_count = 0

    def _emit(self, level, msg):
        self.log_queue.put((level, f"[{self.proxy_label}] {msg}"))

    def clientconnect(self, layer):
        self._hook_count += 1
        self._emit("info", f"[钩子#{self._hook_count}] clientconnect")

    def requestheaders(self, flow):
        self._hook_count += 1
        self._emit("info",
            f"[钩子#{self._hook_count}] requestheaders {flow.request.method} {flow.request.pretty_url}")

    def request(self, flow):
        self._hook_count += 1
        self._emit("info",
            f"[钩子#{self._hook_count}] request flow=#{flow.id[:8]} {flow.request.method} {flow.request.pretty_url}")

    def running(self):
        if self._ready_event:
            self._ready_event.set()
        self._emit("info", "代理已启动，监听端口已就绪")

    def done(self):
        self._emit("info", "代理已关闭")

    def log(self, entry):
        level = getattr(entry, "level", None) or "info"
        msg = getattr(entry, "msg", None) or str(entry)

        if level in ("debug",):
            return
        if msg and level == "info":
            low = msg.lower()
            if low.startswith(_NOISY_PREFIXES):
                return

        self.log_queue.put((level, f"[{self.proxy_label}] {msg}"))

    def error(self, flow):
        msg = str(flow.error)
        if "Connection-specific header field" in msg:
            return
        if "HTTP/2 protocol error" in msg:
            return
        self._emit("error", f"{flow.error}")

    def server_connect_error(self, data):
        self._emit("warning", f"上游连接失败: {data}")


class ScriptAddon:
    """Loads the generated addon module and auto-reloads when the file changes."""

    def __init__(self, script_path, logger=None):
        self.script_path = script_path
        self._logger = logger or logging.getLogger("mitmproxy")
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
        except Exception as e:
            self._logger.error(
                "Failed to load addon script %s: %s\n%s",
                self.script_path, e, traceback.format_exc()
            )
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
                    self._logger.info("[ScriptAddon] dispatching request #%s to %s",
                                     flow.id[:8], type(addon).__name__)
                    addon.request(flow)

    def response(self, flow):
        self._maybe_reload()
        if self.module:
            for addon in getattr(self.module, "addons", []):
                if hasattr(addon, "response"):
                    self._logger.info("[ScriptAddon] dispatching response #%s to %s",
                                     flow.id[:8], type(addon).__name__)
                    addon.response(flow)

    def error(self, flow):
        self._maybe_reload()
        if self.module:
            for addon in getattr(self.module, "addons", []):
                if hasattr(addon, "error"):
                    addon.error(flow)


def run_proxy_worker(config, log_queue, ready_event, shutdown_event):
    """Entry point for the worker process.

    Sets up and runs a mitmproxy Master in an isolated asyncio event loop.
    Logs are forwarded to the main process via log_queue.

    config dict keys:
        name, instance_id, port, listen_host, addon_script_path,
        ssl_insecure, http2, ssl_verify_upstream_trusted_ca
    """
    name = config["name"]
    instance_id = config["instance_id"]
    proxy_label = f"{name}#{instance_id}"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    opts = options.Options(
        listen_host=config["listen_host"],
        listen_port=config["port"],
        ssl_insecure=config["ssl_insecure"],
        http2=config["http2"],
    )

    if config.get("ssl_verify_upstream_trusted_ca"):
        opts.update(
            ssl_verify_upstream_trusted_ca=config["ssl_verify_upstream_trusted_ca"]
        )

    async def run_proxy():
        master = Master(opts)
        master.addons.add(*default_addons())
        master.addons.add(ConnectionHeaderCleaner())

        # Logging via Queue
        master.addons.add(QueueProxyLogAddon(proxy_label, log_queue, ready_event))
        channel = f"mitmproxy_addon_{name.lower()}"
        addon_logger = logging.getLogger(channel)
        addon_logger.setLevel(logging.INFO)
        addon_logger.propagate = False
        log_handler = QueueLogHandler(proxy_label, log_queue)
        log_handler.setFormatter(logging.Formatter("%(message)s"))
        addon_logger.addHandler(log_handler)

        # Generated addon script
        script_path = config.get("addon_script_path", "")
        if script_path:
            try:
                master.addons.add(ScriptAddon(script_path, addon_logger))
            except Exception as e:
                addon_logger.error("Failed to load addon script: %s\n%s", e,
                                  traceback.format_exc())

        # Poll shutdown event from the event loop (no extra thread needed)
        async def _watch_shutdown():
            while not shutdown_event.is_set():
                await asyncio.sleep(0.5)
            master.shutdown()

        asyncio.ensure_future(_watch_shutdown())
        await master.run()

    try:
        loop.run_until_complete(run_proxy())
    except Exception as e:
        log_queue.put(("error",
            f"[{proxy_label}] 事件循环异常: {e}\n{traceback.format_exc()}"))
    finally:
        try:
            loop.close()
        except Exception:
            pass
