import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTabWidget,
    QMenuBar, QMenu, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from gui.styles import DARK_STYLESHEET
from gui.proxy_control import ProxyControl
from gui.rule_panel import RulePanel
from gui.script_editor import ScriptEditorWidget
from gui.log_viewer import LogViewer
from gui.cert_dialog import CertDialog
from gui.settings_dialog import SettingsDialog
from core.config_manager import ConfigManager
from core.rule_engine import RuleEngine
from core.proxy_manager import ProxyManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mitmproxy 代理工具")
        self.setMinimumSize(1000, 700)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, "config.json")
        self.rules_path = os.path.join(base_dir, "rules.json")
        self.scripts_dir = os.path.join(base_dir, "scripts")
        self.generated_dir = os.path.join(base_dir, "generated")

        self.config_manager = ConfigManager(self.config_path)
        self.rule_engine = RuleEngine(self.rules_path)
        self.proxy_manager = ProxyManager(self.generated_dir)

        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
        self._load_state()

    def _setup_ui(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        cert_action = QAction("证书管理", self)
        cert_action.triggered.connect(self._open_cert_dialog)
        file_menu.addAction(cert_action)

        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self.proxy_control = ProxyControl()
        main_layout.addWidget(self.proxy_control)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.rule_panel = RulePanel(self.rule_engine, self.scripts_dir)
        self.tab_widget.addTab(self.rule_panel, "规则")

        script_container = QWidget()
        script_layout = QVBoxLayout(script_container)
        script_layout.setContentsMargins(0, 0, 0, 0)
        self.script_editor = ScriptEditorWidget()
        script_layout.addWidget(self.script_editor)
        self.tab_widget.addTab(script_container, "脚本编辑器")

        self.log_viewer = LogViewer()
        self.tab_widget.addTab(self.log_viewer, "日志")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 | 代理: 已停止 | 规则: 0")

    def _apply_theme(self):
        self.setStyleSheet(DARK_STYLESHEET)

    def _connect_signals(self):
        self.proxy_control.start_proxy1_signal.connect(self._start_proxy1)
        self.proxy_control.stop_proxy1_signal.connect(self._stop_proxy1)
        self.proxy_control.start_proxy2_signal.connect(self._start_proxy2)
        self.proxy_control.stop_proxy2_signal.connect(self._stop_proxy2)
        self.rule_panel.rule_changed.connect(self._on_rules_changed)
        self.rule_panel.edit_script_requested.connect(self._open_script_in_editor)
        self.script_editor.script_modified.connect(self._on_script_saved)

    def _load_state(self):
        self.proxy_control.load_config(self.config_manager.config)
        self._update_status_bar()

    def _update_status_bar(self):
        p1 = "运行中" if self.proxy_manager.proxy1_running else "已停止"
        p2 = "运行中" if self.proxy_manager.proxy2_running else "已停止"
        total = len(self.rule_engine.rules)
        enabled = len([r for r in self.rule_engine.rules if r.enabled])
        self.status_bar.showMessage(f"代理1: {p1} | 代理2: {p2} | 规则: {enabled}/{total} 启用")

    def _start_proxy1(self):
        cfg = self.proxy_control.get_proxy1_config()
        ok, msg = self.proxy_manager.start_proxy1(
            port=cfg["port"],
            listen_host=cfg["host"],
            upstream=cfg["upstream"],
            rules=self.rule_engine.rules,
            scripts_dir=self.scripts_dir,
            proxy_settings=self.config_manager.get_settings(),
            log_callback=self.log_viewer.add_log
        )
        if ok:
            self.proxy_control.set_proxy1_running(True)
            self.log_viewer.add_log(msg)
        else:
            QMessageBox.warning(self, "代理1", msg)
        self._update_status_bar()

    def _stop_proxy1(self):
        ok, msg = self.proxy_manager.stop_proxy1()
        if ok:
            self.proxy_control.set_proxy1_running(False)
            self.log_viewer.add_log(msg)
        else:
            QMessageBox.warning(self, "代理1", msg)
        self._update_status_bar()

    def _start_proxy2(self):
        cfg = self.proxy_control.get_proxy2_config()
        ok, msg = self.proxy_manager.start_proxy2(
            port=cfg["port"],
            listen_host=cfg["host"],
            upstream=cfg["upstream"],
            rules=self.rule_engine.rules,
            scripts_dir=self.scripts_dir,
            proxy_settings=self.config_manager.get_settings(),
            log_callback=self.log_viewer.add_log
        )
        if ok:
            self.proxy_control.set_proxy2_running(True)
            self.log_viewer.add_log(msg)
        else:
            QMessageBox.warning(self, "代理2", msg)
        self._update_status_bar()

    def _stop_proxy2(self):
        ok, msg = self.proxy_manager.stop_proxy2()
        if ok:
            self.proxy_control.set_proxy2_running(False)
            self.log_viewer.add_log(msg)
        else:
            QMessageBox.warning(self, "代理2", msg)
        self._update_status_bar()

    def _on_rules_changed(self):
        self._update_status_bar()
        self._reload_addon_if_running()

    def _on_script_saved(self, _file_path):
        self._reload_addon_if_running()

    def _reload_addon_if_running(self):
        """Regenerate addon scripts and reload running proxies."""
        if self.proxy_manager.proxy1_running:
            from core.addon_generator import generate_addon_script
            addon_path = os.path.join(self.generated_dir, "addon_proxy1.py")
            generate_addon_script(self.rule_engine.rules, "proxy1", self.scripts_dir, addon_path)
            self.log_viewer.add_log("代理1 插件已更新")
        if self.proxy_manager.proxy2_running:
            from core.addon_generator import generate_addon_script
            addon_path = os.path.join(self.generated_dir, "addon_proxy2.py")
            generate_addon_script(self.rule_engine.rules, "proxy2", self.scripts_dir, addon_path)
            self.log_viewer.add_log("代理2 插件已更新")

    def _open_script_in_editor(self, file_path):
        self.script_editor.open_file(file_path)
        self.tab_widget.setCurrentIndex(1)

    def _open_settings(self):
        dialog = SettingsDialog(self.config_manager.config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            self.config_manager.config = new_config
            self.config_manager.save()
            self.proxy_control.load_config(new_config)
            self.log_viewer.add_log("设置已更新，重启代理后生效。")

    def _open_cert_dialog(self):
        dialog = CertDialog(self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "Mitmproxy 代理工具\n\n"
            "管理两个 mitmproxy 实例，支持基于规则的脚本路由。\n"
            "支持请求/响应的加解密处理流水线。"
        )

    def closeEvent(self, event):
        if self.proxy_manager.proxy1_running or self.proxy_manager.proxy2_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "代理正在运行中，停止并退出？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.proxy_manager.stop_all()
                self.log_viewer.add_log("所有代理已停止。")
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
