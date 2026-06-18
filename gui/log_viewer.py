import time
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QBrush, QTextCursor


class LogViewer(QWidget):
    log_signal = Signal(object, str)

    # Color map for log levels
    _LEVEL_COLORS = {
        "error": QColor("#f38ba8"),    # red
        "warning": QColor("#fab387"),  # peach
        "info": QColor("#cdd6f4"),     # text (default)
        "debug": QColor("#6c7086"),    # gray
    }

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

    def add_log(self, message, level="info"):
        """Accept either a plain string or a (level, message) tuple from LogAddon."""
        if isinstance(message, tuple):
            level, message = message
        self.log_signal.emit(level, message)

    @Slot(object, str)
    def _append_log(self, level, message):
        timestamp = time.strftime("%H:%M:%S")
        color = self._LEVEL_COLORS.get(level, self._LEVEL_COLORS["info"])

        ts_fmt = QTextCharFormat()
        ts_fmt.setForeground(QBrush(QColor("#6c7086")))

        msg_fmt = QTextCharFormat()
        msg_fmt.setForeground(QBrush(color))

        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{timestamp}] ", ts_fmt)
        cursor.insertText(message, msg_fmt)
        cursor.insertText("\n", msg_fmt)

        self.log_edit.ensureCursorVisible()

    def _clear_log(self):
        self.log_edit.clear()
