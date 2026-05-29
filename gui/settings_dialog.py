from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox, QLineEdit,
    QDialogButtonBox, QGroupBox, QCheckBox, QFileDialog,
    QHBoxLayout, QPushButton
)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Proxy 1 ---
        p1_group = QGroupBox("代理1 (浏览器 → 解密 → Burp)")
        p1_form = QFormLayout()
        self.p1_port = QSpinBox()
        self.p1_port.setRange(1, 65535)
        self.p1_port.setValue(8081)
        p1_form.addRow("监听端口:", self.p1_port)

        self.p1_host = QLineEdit("127.0.0.1")
        p1_form.addRow("监听地址:", self.p1_host)

        self.p1_upstream = QLineEdit("127.0.0.1:8080")
        p1_form.addRow("上游代理 (Burp):", self.p1_upstream)
        p1_group.setLayout(p1_form)
        layout.addWidget(p1_group)

        # --- Proxy 2 ---
        p2_group = QGroupBox("代理2 (Burp → 加密 → 服务器)")
        p2_form = QFormLayout()
        self.p2_port = QSpinBox()
        self.p2_port.setRange(1, 65535)
        self.p2_port.setValue(8082)
        p2_form.addRow("监听端口:", self.p2_port)

        self.p2_host = QLineEdit("127.0.0.1")
        p2_form.addRow("监听地址:", self.p2_host)

        self.p2_upstream = QLineEdit()
        self.p2_upstream.setPlaceholderText("直连（无上游代理）")
        p2_form.addRow("上游代理:", self.p2_upstream)
        p2_group.setLayout(p2_form)
        layout.addWidget(p2_group)

        # --- Global Settings ---
        settings_group = QGroupBox("全局代理设置")
        settings_form = QFormLayout()

        self.ssl_insecure_cb = QCheckBox("不验证上游 SSL/TLS 证书 (--ssl-insecure)")
        self.ssl_insecure_cb.setToolTip("跳过上游服务器证书验证，Burp 自签名证书场景需要开启")
        settings_form.addRow(self.ssl_insecure_cb)

        self.http2_cb = QCheckBox("启用 HTTP/2 (--http2)")
        self.http2_cb.setToolTip("允许与上游服务器协商 HTTP/2 协议")
        settings_form.addRow(self.http2_cb)

        # CA file for upstream verification
        ca_layout = QHBoxLayout()
        self.ca_file_edit = QLineEdit()
        self.ca_file_edit.setPlaceholderText("留空则不额外指定 CA 文件")
        ca_layout.addWidget(self.ca_file_edit)
        ca_browse_btn = QPushButton("浏览")
        ca_browse_btn.clicked.connect(self._browse_ca)
        ca_layout.addWidget(ca_browse_btn)
        settings_form.addRow("上游 CA 文件:", ca_layout)

        settings_group.setLayout(settings_form)
        layout.addWidget(settings_group)

        # --- Buttons ---
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.Ok).setText("确定")
        btn_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(btn_box)

    def _browse_ca(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 CA 证书文件", "",
            "证书文件 (*.pem *.crt *.cer);;所有文件 (*)"
        )
        if file_path:
            self.ca_file_edit.setText(file_path)

    def _load_config(self):
        p1 = self.config.get("proxy1", {})
        self.p1_port.setValue(p1.get("listen_port", 8081))
        self.p1_host.setText(p1.get("listen_host", "127.0.0.1"))
        self.p1_upstream.setText(p1.get("upstream", "127.0.0.1:8080"))

        p2 = self.config.get("proxy2", {})
        self.p2_port.setValue(p2.get("listen_port", 8082))
        self.p2_host.setText(p2.get("listen_host", "127.0.0.1"))
        self.p2_upstream.setText(p2.get("upstream", ""))

        s = self.config.get("settings", {})
        self.ssl_insecure_cb.setChecked(s.get("ssl_insecure", True))
        self.http2_cb.setChecked(s.get("http2", True))
        self.ca_file_edit.setText(s.get("ssl_verify_upstream_trusted_ca", ""))

    def get_config(self):
        return {
            "proxy1": {
                "listen_port": self.p1_port.value(),
                "listen_host": self.p1_host.text().strip(),
                "upstream": self.p1_upstream.text().strip()
            },
            "proxy2": {
                "listen_port": self.p2_port.value(),
                "listen_host": self.p2_host.text().strip(),
                "upstream": self.p2_upstream.text().strip()
            },
            "settings": {
                "ssl_insecure": self.ssl_insecure_cb.isChecked(),
                "http2": self.http2_cb.isChecked(),
                "ssl_verify_upstream_trusted_ca": self.ca_file_edit.text().strip()
            }
        }
