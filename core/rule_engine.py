import os
import re
import shutil
import yaml

SCRIPT_TEMPLATE = '''"""代理脚本 — {rule_name} ({proxy_label})"""
# _log is injected by the addon loader (proxy-specific channel)
from mitmproxy import ctx


def request(flow):
    _log.info("[{rule_name}] 请求: %s %s", flow.request.method, flow.request.pretty_url)


def response(flow):
    if flow.response:
        _log.info("[{rule_name}] 响应: %s %s", flow.response.status_code, flow.request.pretty_url)
'''

README_TEMPLATE = '''# {rule_name}

## 规则使用方法

### 代理链路

```
浏览器 → Proxy1 (127.0.0.1:8081) → Proxy2 (127.0.0.1:8082) → 目标服务器
```

### 脚本说明

| 脚本 | 位置 | 功能 |
|------|------|------|
| proxy1.py | 解密端 | 在请求解密后、转发前处理请求/响应 |
| proxy2.py | 加密端 | 在请求加密前、发送至目标服务器前处理请求/响应 |

### 使用步骤

1. 在工具中启用 {rule_name} 规则
2. 启动对应代理实例
3. 配置浏览器或应用代理为对应端口
4. 访问匹配 `{url_pattern}` 的目标 URL

### 自定义修改

编辑 `proxy1.py` 或 `proxy2.py` 脚本以自定义请求/响应的处理逻辑。

## 加解密分析

### 目标应用/接口说明

> 待补充：描述目标应用或接口的基本信息、通信协议等。

### 加密机制分析

> 待补充：分析目标应用的加密方式，如：
> - 是否使用 TLS/SSL
> - 是否有应用层自定义加密（如 AES、RSA、签名校验等）
> - 密钥交换方式
> - 证书固定（SSL Pinning）情况

### 加解密流程

```
┌─────────┐     TLS(mitmproxy)     ┌─────────┐     TLS(目标)     ┌─────────┐
│  客户端  │ ◄──────────────────────► │ Proxy1  │ ◄───────────────► │ Proxy2  │ ──► 目标服务器
└─────────┘                         └─────────┘                   └─────────┘
```

### 解密阶段 (Proxy1)

1. 客户端发起请求到 Proxy1
2. Proxy1 使用 mitmproxy CA 证书与客户端完成 TLS 握手
3. 加密请求在 Proxy1 处被解密为明文
4. `proxy1.py` 的 `request()` 在明文上执行，可读取/修改请求内容
5. 修改后的请求转发至 Proxy2

### 加密阶段 (Proxy2)

1. Proxy2 接收来自 Proxy1 的明文请求
2. `proxy2.py` 的 `request()` 可对明文做进一步处理
3. Proxy2 与目标服务器建立 TLS 连接并发送请求
4. 收到响应后，`proxy2.py` 的 `response()` 处理明文响应
5. 响应经 Proxy1 re-encrypt → 客户端

### 关键代码分析

> 待补充：对 proxy1.py / proxy2.py 中关键逻辑的说明。

### 安全说明

- 本规则仅用于安全测试和本地调试
- mitmproxy CA 证书需在客户端设备上手动信任
- 注意保护规则中可能包含的敏感信息（如密钥、Token）
'''


def _sanitize_name(name):
    """Convert a display name to a safe directory name."""
    safe = re.sub(r'[<>:"/\\|?*\s]+', '_', name.strip())
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_').lower() or "untitled"


class Rule:
    def __init__(self, rule_id=None, name="", url_pattern="",
                 proxy1_enabled=True, proxy2_enabled=True):
        self.id = rule_id or _sanitize_name(name)
        self.name = name
        self.url_pattern = url_pattern
        self.proxy1_enabled = proxy1_enabled
        self.proxy2_enabled = proxy2_enabled

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url_pattern": self.url_pattern,
            "proxy1_enabled": self.proxy1_enabled,
            "proxy2_enabled": self.proxy2_enabled,
        }

    @staticmethod
    def from_dict(d, rule_id=None):
        return Rule(
            rule_id=rule_id or d.get("id", ""),
            name=d.get("name", ""),
            url_pattern=d.get("url_pattern", ""),
            proxy1_enabled=d.get("proxy1_enabled", True),
            proxy2_enabled=d.get("proxy2_enabled", True),
        )

    def matches_url(self, url):
        if not self.url_pattern:
            return False
        try:
            return bool(re.search(self.url_pattern, url))
        except re.error:
            return False

    @property
    def is_active(self):
        """Rule is active if at least one proxy script is enabled."""
        return self.proxy1_enabled or self.proxy2_enabled


class RuleEngine:
    def __init__(self, rules_dir):
        self.rules_dir = rules_dir
        self.rules = []
        self.load()

    def _rule_dir(self, rule_id):
        return os.path.join(self.rules_dir, rule_id)

    def _config_path(self, rule_id):
        return os.path.join(self._rule_dir(rule_id), "config.yml")

    def _script_path(self, rule_id, proxy_key):
        filename = "proxy1.py" if proxy_key in ("proxy1", "script1") else "proxy2.py"
        return os.path.join(self._rule_dir(rule_id), filename)

    def load(self):
        self.rules = []
        if not os.path.isdir(self.rules_dir):
            os.makedirs(self.rules_dir, exist_ok=True)
            return

        for entry in sorted(os.listdir(self.rules_dir)):
            rule_dir = os.path.join(self.rules_dir, entry)
            if not os.path.isdir(rule_dir):
                continue
            config_path = os.path.join(rule_dir, "config.yml")
            if not os.path.isfile(config_path):
                continue
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                rule = Rule.from_dict(data, rule_id=entry)
                self.rules.append(rule)
            except Exception:
                continue

    def _save_rule_config(self, rule):
        os.makedirs(self._rule_dir(rule.id), exist_ok=True)
        config_path = self._config_path(rule.id)
        data = {
            "name": rule.name,
            "url_pattern": rule.url_pattern,
            "proxy1_enabled": rule.proxy1_enabled,
            "proxy2_enabled": rule.proxy2_enabled,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, indent=2, allow_unicode=True,
                           default_flow_style=False, sort_keys=False)

    def _write_template_script(self, rule_id, proxy_key):
        rule = self.get_rule(rule_id)
        name = rule.name if rule else rule_id
        label = "代理1" if proxy_key in ("proxy1", "script1") else "代理2"
        script_path = self._script_path(rule_id, proxy_key)
        if not os.path.exists(script_path):
            content = SCRIPT_TEMPLATE.format(rule_name=name, proxy_label=label)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(content)

    def _write_readme(self, rule_id):
        rule = self.get_rule(rule_id)
        name = rule.name if rule else rule_id
        url_pattern = rule.url_pattern if rule else ""
        readme_path = os.path.join(self._rule_dir(rule_id), "readme.md")
        if not os.path.exists(readme_path):
            content = README_TEMPLATE.format(rule_name=name, url_pattern=url_pattern)
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)

    def save(self):
        """Persist all rules to disk."""
        for rule in self.rules:
            self._save_rule_config(rule)

    def add_rule(self, rule):
        base_id = rule.id or _sanitize_name(rule.name)
        rule.id = base_id
        counter = 1
        while os.path.exists(self._rule_dir(rule.id)):
            rule.id = f"{base_id}_{counter}"
            counter += 1

        os.makedirs(self._rule_dir(rule.id), exist_ok=True)
        self._save_rule_config(rule)
        self._write_template_script(rule.id, "proxy1")
        self._write_template_script(rule.id, "proxy2")
        self._write_readme(rule.id)
        self.rules.append(rule)
        return rule

    def update_rule(self, rule_id, **kwargs):
        for i, r in enumerate(self.rules):
            if r.id == rule_id:
                old_name = r.name
                old_id = r.id
                for key, value in kwargs.items():
                    if hasattr(r, key):
                        setattr(r, key, value)

                # Rename directory if name changed and new id differs
                new_id = _sanitize_name(r.name)
                if new_id != old_id:
                    old_dir = self._rule_dir(old_id)
                    # Ensure unique new id
                    base_id = new_id
                    counter = 1
                    while os.path.exists(self._rule_dir(new_id)) and new_id != old_id:
                        new_id = f"{base_id}_{counter}"
                        counter += 1
                    new_dir = self._rule_dir(new_id)
                    if os.path.isdir(old_dir):
                        os.rename(old_dir, new_dir)
                    r.id = new_id

                self._save_rule_config(r)
                return r
        return None

    def delete_rule(self, rule_id):
        self.rules = [r for r in self.rules if r.id != rule_id]
        rule_dir = self._rule_dir(rule_id)
        if os.path.isdir(rule_dir):
            shutil.rmtree(rule_dir)

    def get_rule(self, rule_id):
        for r in self.rules:
            if r.id == rule_id:
                return r
        return None

    def get_active_rules(self):
        """Rules with at least one proxy script enabled."""
        return [r for r in self.rules if r.is_active]

    def find_matching_rule(self, url):
        for r in self.rules:
            if r.matches_url(url):
                return r
        return None

    def get_rules_dir(self):
        return self.rules_dir

    def get_rule_script_path(self, rule_id, proxy_key):
        """Get absolute path to proxy1.py or proxy2.py for a rule."""
        return self._script_path(rule_id, proxy_key)


def migrate_from_legacy(source_dir, user_data_dir):
    """
    Migrate old rules.json + scripts/ structure to new rules/ directory structure.
    source_dir: where old rules.json and scripts/ may reside.
    user_data_dir: where the new rules/ directory will be created.
    Returns True if migration was performed.
    """
    import json
    old_rules_path = os.path.join(source_dir, "rules.json")
    old_scripts_dir = os.path.join(source_dir, "scripts")
    new_rules_dir = os.path.join(user_data_dir, "rules")

    if not os.path.exists(old_rules_path):
        return False

    if os.path.isdir(new_rules_dir) and os.listdir(new_rules_dir):
        return False

    try:
        with open(old_rules_path, "r", encoding="utf-8") as f:
            old_rules = json.load(f)
    except Exception:
        return False

    os.makedirs(new_rules_dir, exist_ok=True)

    for old_rule in old_rules:
        name = old_rule.get("name", "untitled")
        rule_id = _sanitize_name(name)

        counter = 1
        while os.path.exists(os.path.join(new_rules_dir, rule_id)):
            rule_id = f"{_sanitize_name(name)}_{counter}"
            counter += 1

        rule_dir = os.path.join(new_rules_dir, rule_id)
        os.makedirs(rule_dir, exist_ok=True)

        had_script1 = bool(old_rule.get("script_proxy1"))
        had_script2 = bool(old_rule.get("script_proxy2"))

        config = {
            "name": name,
            "url_pattern": old_rule.get("url_pattern", ""),
            "proxy1_enabled": had_script1,
            "proxy2_enabled": had_script2,
        }
        with open(os.path.join(rule_dir, "config.yml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, indent=2, allow_unicode=True,
                           default_flow_style=False, sort_keys=False)

        for key, script_rel in [("proxy1", old_rule.get("script_proxy1", "")),
                                 ("proxy2", old_rule.get("script_proxy2", ""))]:
            target = os.path.join(rule_dir, f"{key}.py")
            if script_rel:
                src = os.path.join(old_scripts_dir, script_rel)
                if os.path.exists(src):
                    shutil.copy2(src, target)
                    continue
            with open(target, "w", encoding="utf-8") as f:
                f.write(f'"""代理脚本 — {name}"""\nfrom mitmproxy import ctx\n\n'
                        f'def request(flow):\n    pass\n\n'
                        f'def response(flow):\n    pass\n')

    bak_rules = old_rules_path + ".bak"
    bak_scripts = old_scripts_dir + ".bak"
    try:
        os.rename(old_rules_path, bak_rules)
    except OSError:
        pass
    try:
        if os.path.isdir(old_scripts_dir):
            os.rename(old_scripts_dir, bak_scripts)
    except OSError:
        pass

    return True
