import os
import shutil
import tempfile
import zipfile

import yaml


def export_rule_to_zip(rule, rules_dir, output_path):
    """
    Export a single rule directory to a zip file.
    The zip contains the rule's proxy1.py, proxy2.py, and config.yml.
    """
    rule_dir = os.path.join(rules_dir, rule.id)
    if not os.path.isdir(rule_dir):
        return False, f"规则目录不存在: {rule_dir}"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in ["proxy1.py", "proxy2.py", "config.yml", "readme.md"]:
            file_path = os.path.join(rule_dir, filename)
            if os.path.exists(file_path):
                zf.write(file_path, filename)
            else:
                # Include empty placeholder for missing optional scripts
                if filename != "config.yml":
                    zf.writestr(filename, f'"""占位脚本 — {filename}"""\n')

    return True, f"已导出至 {output_path}"


def import_rule_from_zip(zip_path, rules_dir):
    """
    Import a rule from a zip file.
    Extracts to rules/<name>/ directory, auto-renaming if duplicate.
    Returns (rule_data_dict, error_string).
    """
    # Validate zip
    if not os.path.exists(zip_path):
        return None, "文件不存在"

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Check for config.yml
            names = zf.namelist()
            if "config.yml" not in names:
                return None, "无效的规则包: 缺少 config.yml"

            zf.extractall(tmpdir)

        # Read config
        config_path = os.path.join(tmpdir, "config.yml")
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Determine rule directory name from config or zip filename
        rule_name = config.get("name", "")
        if not rule_name:
            rule_name = os.path.splitext(os.path.basename(zip_path))[0]

        from core.rule_engine import _sanitize_name
        dir_name = _sanitize_name(rule_name)
        target_dir = os.path.join(rules_dir, dir_name)

        # Auto-rename if exists
        counter = 1
        while os.path.exists(target_dir):
            dir_name = f"{_sanitize_name(rule_name)}_{counter}"
            target_dir = os.path.join(rules_dir, dir_name)
            counter += 1

        # Copy all files
        os.makedirs(target_dir, exist_ok=True)
        for filename in os.listdir(tmpdir):
            src = os.path.join(tmpdir, filename)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(target_dir, filename))

        # Ensure missing template files exist
        for script_file in ["proxy1.py", "proxy2.py"]:
            sp = os.path.join(target_dir, script_file)
            if not os.path.exists(sp):
                with open(sp, "w", encoding="utf-8") as f:
                    f.write(f'"""代理脚本 — {rule_name}"""\nfrom mitmproxy import ctx\n\n'
                            f'def request(flow):\n    pass\n\n'
                            f'def response(flow):\n    pass\n')

        readme_path = os.path.join(target_dir, "readme.md")
        if not os.path.exists(readme_path):
            url_pattern = config.get("url_pattern", "")
            from core.rule_engine import README_TEMPLATE
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(README_TEMPLATE.format(rule_name=rule_name, url_pattern=url_pattern))

        # Update config with correct id
        config["id"] = dir_name
        config.setdefault("name", rule_name)
        config.setdefault("url_pattern", "")
        config.setdefault("proxy1_enabled", True)
        config.setdefault("proxy2_enabled", True)
        config.setdefault("enabled", True)

        with open(os.path.join(target_dir, "config.yml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, indent=2, allow_unicode=True,
                           default_flow_style=False, sort_keys=False)

        return config, None
