from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QSpinBox, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal


class ProxyControl(QWidget):
    start_proxy1_signal = Signal()
    stop_proxy1_signal = Signal()
    start_proxy2_signal = Signal()
    stop_proxy2_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxy1_running = False
        self.proxy2_running = False
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Proxy 1
        proxy1_group = QGroupBox("代理1 — 浏览器 → 解密 → Burp")
        p1_layout = QVBoxLayout(proxy1_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("监听:"))
        self.p1_host = QLineEdit("127.0.0.1")
        self.p1_host.setFixedWidth(100)
        row1.addWidget(QLabel("地址:"))
        row1.addWidget(self.p1_host)
        row1.addWidget(QLabel("端口:"))
        self.p1_port = QSpinBox()
        self.p1_port.setRange(1, 65535)
        self.p1_port.setValue(8081)
        self.p1_port.setFixedWidth(80)
        row1.addWidget(self.p1_port)
        row1.addWidget(QLabel("上游 (Burp):"))
        self.p1_upstream = QLineEdit("127.0.0.1:8080")
        self.p1_upstream.setFixedWidth(120)
        row1.addWidget(self.p1_upstream)
        row1.addStretch()
        p1_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.p1_status = QLabel("已停止")
        self.p1_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
        row2.addWidget(self.p1_status)

        self.p1_start_btn = QPushButton("启动")
        self.p1_start_btn.setObjectName("startBtn")
        self.p1_start_btn.clicked.connect(lambda: self.start_proxy1_signal.emit())
        self.p1_stop_btn = QPushButton("停止")
        self.p1_stop_btn.setObjectName("stopBtn")
        self.p1_stop_btn.clicked.connect(lambda: self.stop_proxy1_signal.emit())
        self.p1_stop_btn.setEnabled(False)
        row2.addWidget(self.p1_start_btn)
        row2.addWidget(self.p1_stop_btn)
        row2.addStretch()
        p1_layout.addLayout(row2)

        main_layout.addWidget(proxy1_group)

        # Proxy 2
        proxy2_group = QGroupBox("代理2 — Burp → 加密 → 服务器")
        p2_layout = QVBoxLayout(proxy2_group)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("监听:"))
        self.p2_host = QLineEdit("127.0.0.1")
        self.p2_host.setFixedWidth(100)
        row3.addWidget(QLabel("地址:"))
        row3.addWidget(self.p2_host)
        row3.addWidget(QLabel("端口:"))
        self.p2_port = QSpinBox()
        self.p2_port.setRange(1, 65535)
        self.p2_port.setValue(8082)
        self.p2_port.setFixedWidth(80)
        row3.addWidget(self.p2_port)
        row3.addWidget(QLabel("上游:"))
        self.p2_upstream = QLineEdit("")
        self.p2_upstream.setPlaceholderText("直连（无上游）")
        self.p2_upstream.setFixedWidth(140)
        row3.addWidget(self.p2_upstream)
        row3.addStretch()
        p2_layout.addLayout(row3)

        row4 = QHBoxLayout()
        self.p2_status = QLabel("已停止")
        self.p2_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
        row4.addWidget(self.p2_status)

        self.p2_start_btn = QPushButton("启动")
        self.p2_start_btn.setObjectName("startBtn")
        self.p2_start_btn.clicked.connect(lambda: self.start_proxy2_signal.emit())
        self.p2_stop_btn = QPushButton("停止")
        self.p2_stop_btn.setObjectName("stopBtn")
        self.p2_stop_btn.clicked.connect(lambda: self.stop_proxy2_signal.emit())
        self.p2_stop_btn.setEnabled(False)
        row4.addWidget(self.p2_start_btn)
        row4.addWidget(self.p2_stop_btn)
        row4.addStretch()
        p2_layout.addLayout(row4)

        main_layout.addWidget(proxy2_group)

    def set_proxy1_running(self, running):
        self.proxy1_running = running
        if running:
            self.p1_status.setText("运行中")
            self.p1_status.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.p1_start_btn.setEnabled(False)
            self.p1_stop_btn.setEnabled(True)
        else:
            self.p1_status.setText("已停止")
            self.p1_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
            self.p1_start_btn.setEnabled(True)
            self.p1_stop_btn.setEnabled(False)

    def set_proxy2_running(self, running):
        self.proxy2_running = running
        if running:
            self.p2_status.setText("运行中")
            self.p2_status.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.p2_start_btn.setEnabled(False)
            self.p2_stop_btn.setEnabled(True)
        else:
            self.p2_status.setText("已停止")
            self.p2_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
            self.p2_start_btn.setEnabled(True)
            self.p2_stop_btn.setEnabled(False)

    def get_proxy1_config(self):
        return {
            "port": self.p1_port.value(),
            "host": self.p1_host.text().strip(),
            "upstream": self.p1_upstream.text().strip()
        }

    def get_proxy2_config(self):
        return {
            "port": self.p2_port.value(),
            "host": self.p2_host.text().strip(),
            "upstream": self.p2_upstream.text().strip()
        }

    def load_config(self, config):
        p1 = config.get("proxy1", {})
        self.p1_port.setValue(p1.get("listen_port", 8081))
        self.p1_host.setText(p1.get("listen_host", "127.0.0.1"))
        self.p1_upstream.setText(p1.get("upstream", "127.0.0.1:8080"))

        p2 = config.get("proxy2", {})
        self.p2_port.setValue(p2.get("listen_port", 8082))
        self.p2_host.setText(p2.get("listen_host", "127.0.0.1"))
        self.p2_upstream.setText(p2.get("upstream", ""))
