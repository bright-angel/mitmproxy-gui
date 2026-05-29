import os
import textwrap


def generate_addon_script(rules, proxy_key, scripts_dir, output_path):
    """
    Generate a combined mitmproxy addon script for a proxy instance.

    proxy_key: "proxy1" or "proxy2" — which script to load per rule.
    scripts_dir: base directory for resolving relative script paths.
    """
    enabled_rules = [r for r in rules if r.enabled]
    script_field = "script_proxy1" if proxy_key == "proxy1" else "script_proxy2"

    lines = [
        '"""Generated mitmproxy addon — do not edit manually."""',
        'import os',
        'import sys',
        'import importlib.util',
        'from mitmproxy import ctx',
        '',
        '_RULES = [',
    ]

    for rule in enabled_rules:
        rel_path = getattr(rule, script_field)
        if not rel_path:
            continue
        abs_path = os.path.join(scripts_dir, rel_path)
        if not os.path.exists(abs_path):
            continue
        abs_path_escaped = abs_path.replace("\\", "\\\\")
        lines.append('    {')
        lines.append(f'        "id": "{rule.id}",')
        lines.append(f'        "name": "{rule.name}",')
        lines.append(f'        "pattern": r"{rule.url_pattern}",')
        lines.append(f'        "script_path": "{abs_path_escaped}",')
        lines.append('    },')

    lines.append(']')
    lines.append('')
    lines.append(textwrap.dedent('''
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
            sys.modules[f"rule_script_{abs(hash(script_path))}"] = module
            _MTIME_CACHE[script_path] = mtime
            return module
        except Exception as e:
            ctx.log.error(f"Failed to load script {script_path}: {e}")
            return None

    class RuleDispatcher:
        def request(self, flow):
            import re
            url = flow.request.pretty_url
            for rule in _RULES:
                try:
                    if re.search(rule["pattern"], url):
                        ctx.log.info(f"[命中规则] {rule['name']} — 请求: {flow.request.method} {url}")
                        module = _load_module(rule["script_path"])
                        if module and hasattr(module, "request"):
                            module.request(flow)
                        return
                except re.error:
                    continue

        def response(self, flow):
            import re
            url = flow.request.pretty_url
            for rule in _RULES:
                try:
                    if re.search(rule["pattern"], url):
                        ctx.log.info(f"[命中规则] {rule['name']} — 响应: {flow.response.status_code} {url}")
                        module = _load_module(rule["script_path"])
                        if module and hasattr(module, "response"):
                            module.response(flow)
                        return
                except re.error:
                    continue

    addons = [RuleDispatcher()]
    '''))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
