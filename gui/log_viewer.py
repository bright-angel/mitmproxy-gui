import time
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, QTimer, Signal, Slot


class LogViewer(QWidget):
    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.log_signal.connect(self._append_log)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        clear_btn = QPushButton("清空")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._clear_log)
        toolbar.addStretch()
        toolbar.addWidget(clear_btn)
        layout.addLayout(toolbar)

        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(5000)
        self.log_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.log_edit)

    def add_log(self, message):
        self.log_signal.emit(message)

    @Slot(str)
    def _append_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_edit.appendPlainText(f"[{timestamp}] {message}")

    def _clear_log(self):
        self.log_edit.clear()
