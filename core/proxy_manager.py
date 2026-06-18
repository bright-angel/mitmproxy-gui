import multiprocessing
import os
import threading

from .proxy_worker import run_proxy_worker


class ProxyInstance:
    """Manages a mitmproxy Master running in a separate process.

    Each proxy instance runs in its own multiprocessing.Process to avoid
    the mitmproxy.ctx.master module-level global conflict that prevents
    two Masters from coexisting in one Python process.
    """

    _instance_counter = 0

    def __init__(self, name, port, listen_host, upstream, addon_script_path,
                 proxy_settings=None, log_callback=None):
        ProxyInstance._instance_counter += 1
        self._id = ProxyInstance._instance_counter
        self.name = name
        self.port = port
        self.listen_host = listen_host
        self.upstream = upstream
        self.addon_script_path = addon_script_path
        self.proxy_settings = proxy_settings or {}
        self.log_callback = log_callback

        self._process = None
        self._log_queue = None
        self._ready_event = None
        self._shutdown_event = None
        self._reader_thread = None
        self._reader_stop = None
        self._running = False

    @property
    def is_running(self):
        return self._running and self._process is not None and self._process.is_alive()

    def start(self):
        if self.is_running:
            return False, f"{self.name}#{self._id} 已在运行中"

        self._log_queue = multiprocessing.Queue()
        self._ready_event = multiprocessing.Event()
        self._shutdown_event = multiprocessing.Event()
        self._reader_stop = threading.Event()

        s = self.proxy_settings
        config = {
            "name": self.name,
            "instance_id": self._id,
            "port": self.port,
            "listen_host": self.listen_host,
            "addon_script_path": self.addon_script_path,
            "ssl_insecure": s.get("ssl_insecure", True),
            "http2": s.get("http2", True),
            "ssl_verify_upstream_trusted_ca": s.get("ssl_verify_upstream_trusted_ca", ""),
        }

        self._process = multiprocessing.Process(
            target=run_proxy_worker,
            args=(config, self._log_queue, self._ready_event, self._shutdown_event),
            daemon=True
        )
        self._process.start()

        # Reader thread: forwards log messages from worker queue to callback
        self._reader_thread = threading.Thread(target=self._read_logs, daemon=True)
        self._reader_thread.start()

        if not self._ready_event.wait(timeout=5.0):
            self._running = False
            self._shutdown_event.set()
            self._cleanup_process()
            return False, f"{self.name}#{self._id} 启动超时 ({self.listen_host}:{self.port})，端口可能被占用"

        self._running = True
        return True, f"{self.name}#{self._id} 已启动 ({self.listen_host}:{self.port})"

    def stop(self):
        if not self.is_running:
            return False, f"{self.name}#{self._id} 未在运行"

        self._running = False
        self._shutdown_event.set()
        self._cleanup_process()

        # Drain remaining log messages, then stop reader thread
        self._drain_log_queue()
        self._reader_stop.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)

        self._process = None
        self._log_queue = None
        self._ready_event = None
        self._shutdown_event = None
        self._reader_thread = None

        return True, f"{self.name}#{self._id} 已停止"

    def _cleanup_process(self):
        if self._process is None:
            return
        if self._process.is_alive():
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=2)

    def _read_logs(self):
        """Forward log messages from worker process to the GUI callback."""
        while not self._reader_stop.is_set():
            try:
                msg = self._log_queue.get(timeout=0.3)
                if msg is None:  # sentinel
                    break
                if self.log_callback:
                    self.log_callback(msg)
            except Exception:
                continue

    def _drain_log_queue(self):
        """Read any remaining log messages after worker exits."""
        while True:
            try:
                msg = self._log_queue.get_nowait()
                if msg is not None and self.log_callback:
                    self.log_callback(msg)
            except Exception:
                break


class ProxyManager:
    def __init__(self, generated_dir):
        self.generated_dir = generated_dir
        self.proxy1 = None
        self.proxy2 = None

    def start_proxy1(self, port, listen_host, upstream, rules, rules_dir,
                     proxy_settings=None, log_callback=None,
                     upstream_enabled=True):
        # Stop any existing instance first to prevent zombie processes
        if self.proxy1 is not None:
            self.proxy1.stop()
        addon_path = os.path.join(self.generated_dir, "addon_proxy1.py")
        from .addon_generator import generate_addon_script
        effective_upstream = upstream if upstream_enabled else ""
        generate_addon_script(rules, "proxy1", rules_dir, addon_path,
                             upstream=effective_upstream)
        self.proxy1 = ProxyInstance("Proxy1", port, listen_host,
                                    "", addon_path,  # upstream handled in addon
                                    proxy_settings, log_callback)
        return self.proxy1.start()

    def start_proxy2(self, port, listen_host, upstream, rules, rules_dir,
                     proxy_settings=None, log_callback=None,
                     upstream_enabled=True):
        # Stop any existing instance first to prevent zombie processes
        if self.proxy2 is not None:
            self.proxy2.stop()
        addon_path = os.path.join(self.generated_dir, "addon_proxy2.py")
        from .addon_generator import generate_addon_script
        effective_upstream = upstream if upstream_enabled else ""
        generate_addon_script(rules, "proxy2", rules_dir, addon_path,
                             upstream=effective_upstream)
        self.proxy2 = ProxyInstance("Proxy2", port, listen_host,
                                    "", addon_path,  # upstream handled in addon
                                    proxy_settings, log_callback)
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
