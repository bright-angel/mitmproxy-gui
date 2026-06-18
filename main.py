import sys
import os
import shutil


def get_app_dir():
    """Application directory — works in dev and PyInstaller builds."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_user_data_dir():
    """Runtime user data directory."""
    return os.path.join(os.path.expanduser("~"), ".MitmproxyTool")


def first_run_setup(app_dir, user_data_dir):
    """Copy default config and example rules on first run."""
    os.makedirs(user_data_dir, exist_ok=True)

    # Copy config.yml from app template
    user_config = os.path.join(user_data_dir, "config.yml")
    if not os.path.exists(user_config):
        app_config = os.path.join(app_dir, "config.yml")
        if os.path.exists(app_config):
            shutil.copy2(app_config, user_config)

    # Copy example rules from app bundle
    user_rules = os.path.join(user_data_dir, "rules")
    if not os.path.exists(user_rules):
        app_rules = os.path.join(app_dir, "rules")
        if os.path.isdir(app_rules):
            shutil.copytree(app_rules, user_rules)

    os.makedirs(os.path.join(user_data_dir, "generated"), exist_ok=True)

    # Legacy migration: check for old rules.json in app dir
    from core.rule_engine import migrate_from_legacy
    if migrate_from_legacy(app_dir, user_data_dir):
        print("已从旧格式 (rules.json) 迁移规则到用户目录")


def main():
    import multiprocessing
    multiprocessing.freeze_support()
    app_dir = get_app_dir()
    user_data_dir = get_user_data_dir()
    first_run_setup(app_dir, user_data_dir)

    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("MitmproxyTool")
    app.setOrganizationName("ProxyTool")

    window = MainWindow(user_data_dir=user_data_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
