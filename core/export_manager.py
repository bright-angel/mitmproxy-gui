import json
import os
import shutil
import tempfile
import uuid
import zipfile


def export_rule_to_zip(rule, scripts_dir, output_path):
    """
    Export a single rule and its scripts to a zip file.
    Script paths in the rule are relative to scripts_dir.
    Zip contents keep relative structure for round-trip import.
    """
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        rule_data = rule.to_dict()
        zf.writestr("rule.json", json.dumps(rule_data, indent=2, ensure_ascii=False))

        if rule.script_proxy1:
            abs_path = os.path.join(scripts_dir, rule.script_proxy1)
            if os.path.exists(abs_path):
                zf.write(abs_path, f"scripts/{rule.script_proxy1}")
        if rule.script_proxy2:
            abs_path = os.path.join(scripts_dir, rule.script_proxy2)
            if os.path.exists(abs_path):
                zf.write(abs_path, f"scripts/{rule.script_proxy2}")

    return True, f"Exported to {output_path}"


def import_rule_from_zip(zip_path, scripts_dir):
    """
    Import a rule and its scripts from a zip file.
    Scripts are extracted to scripts_dir preserving relative structure.
    Returns (rule_data_dict, error_string).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        rule_json = os.path.join(tmpdir, "rule.json")
        if not os.path.exists(rule_json):
            return None, "Invalid zip: rule.json not found"

        with open(rule_json, "r", encoding="utf-8") as f:
            rule_data = json.load(f)

        extracted_scripts = os.path.join(tmpdir, "scripts")
        if os.path.exists(extracted_scripts):
            for root, dirs, files in os.walk(extracted_scripts):
                for filename in files:
                    src = os.path.join(root, filename)
                    rel = os.path.relpath(src, extracted_scripts)
                    dest = os.path.join(scripts_dir, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)

        rule_data["id"] = str(uuid.uuid4())[:8]
        return rule_data, None
