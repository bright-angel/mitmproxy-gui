import json
import os
import uuid
import re


class Rule:
    def __init__(self, rule_id=None, name="", url_pattern="",
                 script_proxy1="", script_proxy2="", enabled=True):
        self.id = rule_id or str(uuid.uuid4())[:8]
        self.name = name
        self.url_pattern = url_pattern
        self.script_proxy1 = script_proxy1
        self.script_proxy2 = script_proxy2
        self.enabled = enabled

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url_pattern": self.url_pattern,
            "script_proxy1": self.script_proxy1,
            "script_proxy2": self.script_proxy2,
            "enabled": self.enabled
        }

    @staticmethod
    def from_dict(d):
        return Rule(
            rule_id=d.get("id"),
            name=d.get("name", ""),
            url_pattern=d.get("url_pattern", ""),
            script_proxy1=d.get("script_proxy1", ""),
            script_proxy2=d.get("script_proxy2", ""),
            enabled=d.get("enabled", True)
        )

    def matches_url(self, url):
        if not self.enabled or not self.url_pattern:
            return False
        try:
            return bool(re.search(self.url_pattern, url))
        except re.error:
            return False


class RuleEngine:
    def __init__(self, rules_path):
        self.rules_path = rules_path
        self.rules = []
        self.load()

    def load(self):
        if os.path.exists(self.rules_path):
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.rules = [Rule.from_dict(r) for r in data]
        else:
            self.rules = []
            self.save()

    def save(self):
        with open(self.rules_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.rules], f, indent=2, ensure_ascii=False)

    def add_rule(self, rule):
        self.rules.append(rule)
        self.save()
        return rule

    def update_rule(self, rule_id, **kwargs):
        for i, r in enumerate(self.rules):
            if r.id == rule_id:
                for key, value in kwargs.items():
                    if hasattr(r, key):
                        setattr(r, key, value)
                self.save()
                return r
        return None

    def delete_rule(self, rule_id):
        self.rules = [r for r in self.rules if r.id != rule_id]
        self.save()

    def get_rule(self, rule_id):
        for r in self.rules:
            if r.id == rule_id:
                return r
        return None

    def get_enabled_rules(self):
        return [r for r in self.rules if r.enabled]

    def find_matching_rule(self, url):
        for r in self.rules:
            if r.matches_url(url):
                return r
        return None

    def get_scripts_base_dir(self):
        return os.path.join(os.path.dirname(self.rules_path), "scripts")
