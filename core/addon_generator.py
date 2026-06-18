import os
import textwrap


def generate_addon_script(rules, proxy_key, rules_dir, output_path):
    """
    Generate a combined mitmproxy addon script for a proxy instance.

    proxy_key: "proxy1" or "proxy2" — which script to load per rule.
    rules_dir: base directory for rule subdirectories.

    Uses Python's logging module (bypasses mitmproxy ctx.log) so that
    LogHandler attached to the "mitmproxy" logger reliably captures
    every message regardless of how the script is loaded.
    """
    script_file = "proxy1.py" if proxy_key == "proxy1" else "proxy2.py"
    enabled_attr = "proxy1_enabled" if proxy_key == "proxy1" else "proxy2_enabled"

    enabled_rules = [r for r in rules if getattr(r, enabled_attr)]
    channel = f"mitmproxy_addon_{proxy_key}"

    lines = [
        '"""Generated mitmproxy addon — do not edit manually."""',
        'import os',
        'import sys',
        'import logging',
        'import importlib.util',
        '',
        '# Dedicated logger channel per proxy — prevents cross-capture',
        f'_logger = logging.getLogger("{channel}")',
        '',
        '_RULES = [',
    ]

    for rule in enabled_rules:
        script_path = os.path.join(rules_dir, rule.id, script_file)
        if not os.path.exists(script_path):
            continue
        abs_path_escaped = script_path.replace("\\", "\\\\")
        lines.append('    {')
        lines.append(f'        "id": "{rule.id}",')
        lines.append(f'        "name": "{rule.name}",')
        lines.append(f'        "pattern": r"{rule.url_pattern}",')
        lines.append(f'        "script_path": "{abs_path_escaped}",')
        lines.append('    },')
        lines.append('')

    lines.append(']')
    lines.append('')
    lines.append(textwrap.dedent('''
    _logger.info("Addon loaded, %d rule(s) registered", len(_RULES))

    # Per-script mtime cache for hot-reload detection
    _MTIME_CACHE = {}

    def _load_module(script_path):
        """Load a script module, re-importing if file changed on disk."""
        try:
            mtime = os.path.getmtime(script_path)
            if script_path in _MTIME_CACHE:
                if _MTIME_CACHE[script_path] == mtime:
                    return sys.modules.get(f"rule_script_{abs(hash(script_path))}")
        except OSError:
            return None

        try:
            spec = importlib.util.spec_from_file_location(
                f"rule_script_{abs(hash(script_path))}", script_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Inject proxy-specific logger so script logs go to the
            # right channel (no cross-capture between Proxy1 / Proxy2).
            module._log = _logger
            sys.modules[f"rule_script_{abs(hash(script_path))}"] = module
            _MTIME_CACHE[script_path] = mtime
            _logger.info("Loaded script: %s", os.path.basename(script_path))
            return module
        except Exception as e:
            _logger.error("Failed to load script %s: %s", script_path, e)
            return None

    class RuleDispatcher:
        def request(self, flow):
            import re
            url = flow.request.pretty_url
            for rule in _RULES:
                try:
                    if re.search(rule["pattern"], url):
                        _logger.info("[命中规则] %s — 请求: %s %s",
                                     rule["name"], flow.request.method, url)
                        module = _load_module(rule["script_path"])
                        if module and hasattr(module, "request"):
                            try:
                                module.request(flow)
                            except Exception as e:
                                _logger.error("[脚本异常] %s request(): %s",
                                              rule["name"], e)
                        return
                except re.error:
                    continue

        def response(self, flow):
            import re
            url = flow.request.pretty_url
            for rule in _RULES:
                try:
                    if re.search(rule["pattern"], url):
                        _logger.info("[命中规则] %s — 响应: %s %s",
                                     rule["name"], flow.response.status_code, url)
                        module = _load_module(rule["script_path"])
                        if module and hasattr(module, "response"):
                            try:
                                module.response(flow)
                            except Exception as e:
                                _logger.error("[脚本异常] %s response(): %s",
                                              rule["name"], e)
                        return
                except re.error:
                    continue

    addons = [RuleDispatcher()]
    '''))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
