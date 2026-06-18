"""
PyInstaller build script for Mitmproxy GUI Tool.

Usage:
    pip install pyinstaller
    python build.py

Output will be in dist/MitmproxyTool/
"""

import PyInstaller.__main__
import os
import sys


def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    PyInstaller.__main__.run([
        os.path.join(base_dir, "main.py"),
        "--name=MitmproxyTool",
        "--windowed",
        "--onefile",
        "--add-data", f"{base_dir}/config.yml;.",
        "--add-data", f"{base_dir}/rules;rules",
        "--add-data", f"{base_dir}/generated;generated",
        "--hidden-import", "mitmproxy",
        "--hidden-import", "mitmproxy.addons",
        "--hidden-import", "mitmproxy.master",
        "--hidden-import", "mitmproxy.options",
        "--hidden-import", "mitmproxy.proxy",
        "--hidden-import", "mitmproxy.proxy.server",
        "--hidden-import", "yaml",
        "--hidden-import", "core",
        "--hidden-import", "core.config_manager",
        "--hidden-import", "core.proxy_manager",
        "--hidden-import", "core.proxy_worker",
        "--hidden-import", "core.rule_engine",
        "--hidden-import", "core.cert_manager",
        "--hidden-import", "core.addon_generator",
        "--hidden-import", "core.export_manager",
        "--hidden-import", "gui",
        "--hidden-import", "gui.main_window",
        "--hidden-import", "gui.styles",
        "--hidden-import", "gui.proxy_control",
        "--hidden-import", "gui.rule_panel",
        "--hidden-import", "gui.rule_dialog",
        "--hidden-import", "gui.script_editor",
        "--hidden-import", "gui.log_viewer",
        "--hidden-import", "gui.cert_dialog",
        "--hidden-import", "gui.settings_dialog",
        "--collect-all", "mitmproxy",
        "--collect-all", "mitmproxy_rs",
        "--noconfirm",
        "--clean",
    ])


if __name__ == "__main__":
    build()
