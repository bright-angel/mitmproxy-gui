from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt

from core.cert_manager import (
    is_cert_generated, is_cert_installed, install_cert,
    get_mitmproxy_cert_dir
)


class CertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("证书管理")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._refresh_status()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        status_group = QGroupBox("证书状态")
        status_layout = QVBoxLayout(status_group)

        self.generated_label = QLabel()
        self.installed_label = QLabel()
        self.cert_dir_label = QLabel()
        self.cert_dir_label.setTextFormat(Qt.RichText)
        self.cert_dir_label.setOpenExternalLinks(True)

        status_layout.addWidget(self.generated_label)
        status_layout.addWidget(self.installed_label)
        status_layout.addWidget(self.cert_dir_label)
        layout.addWidget(status_group)

        action_layout = QHBoxLayout()
        install_btn = QPushButton("安装证书")
        install_btn.clicked.connect(self._install_cert)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_status)
        action_layout.addWidget(install_btn)
        action_layout.addWidget(refresh_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        info_label = QLabel(
            "安装证书后，请重启浏览器使更改生效。\n"
            "Firefox 需手动导入证书：设置 → 证书。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
        layout.addWidget(info_label)

    def _refresh_status(self):
        generated = is_cert_generated()
        installed = is_cert_installed()
        cert_dir = get_mitmproxy_cert_dir()

        if generated:
            self.generated_label.setText("证书文件: 已找到")
            self.generated_label.setStyleSheet("color: #a6e3a1;")
        else:
            self.generated_label.setText("证书文件: 未找到 (请先启动一次代理以生成证书)")
            self.generated_label.setStyleSheet("color: #f38ba8;")

        if installed:
            self.installed_label.setText("系统信任: 已安装")
            self.installed_label.setStyleSheet("color: #a6e3a1;")
        else:
            self.installed_label.setText("系统信任: 未安装")
            self.installed_label.setStyleSheet("color: #f38ba8;")

        self.cert_dir_label.setText(f"证书目录: {cert_dir}")

    def _install_cert(self):
        if not is_cert_generated():
            QMessageBox.information(
                self, "无证书",
                "未找到证书文件。请先启动一次代理以生成证书，然后再安装。"
            )
            return

        ok, msg = install_cert()
        if ok:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "安装失败", msg)
        self._refresh_status()
