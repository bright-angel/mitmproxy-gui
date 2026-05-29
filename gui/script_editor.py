import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QPlainTextEdit,
    QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#cba6f7"))
        keyword_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal",
            "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
            "True", "False", "None"
        ]
        for kw in keywords:
            self._rules.append((re.compile(rf"\b{kw}\b"), keyword_fmt))

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#a6e3a1"))
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_fmt))
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_fmt))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6c7086"))
        comment_fmt.setFontItalic(True)
        self._rules.append((re.compile(r"#[^\n]*"), comment_fmt))

        decorator_fmt = QTextCharFormat()
        decorator_fmt.setForeground(QColor("#89b4fa"))
        self._rules.append((re.compile(r"@\w+"), decorator_fmt))

        func_fmt = QTextCharFormat()
        func_fmt.setForeground(QColor("#89b4fa"))
        self._rules.append((re.compile(r"\bdef\s+(\w+)"), func_fmt))

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#fab387"))
        self._rules.append((re.compile(r"\b\d+\.?\d*\b"), number_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start(1) if match.lastindex else match.start()
                length = match.end(1) - start if match.lastindex else match.end() - start
                self.setFormat(start, length, fmt)


class ScriptEditorWidget(QWidget):
    script_modified = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self.file_label = QLabel("未打开文件")
        self.file_label.setStyleSheet("color: #a6adc8;")
        toolbar.addWidget(self.file_label)
        toolbar.addStretch()

        new_btn = QPushButton("新建")
        new_btn.clicked.connect(self._new_file)
        open_btn = QPushButton("打开")
        open_btn.clicked.connect(self._open_file)
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_file)
        save_as_btn = QPushButton("另存为")
        save_as_btn.clicked.connect(self._save_as_file)

        toolbar.addWidget(new_btn)
        toolbar.addWidget(open_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(save_as_btn)
        layout.addLayout(toolbar)

        self.editor = QPlainTextEdit()
        self.editor.setTabStopDistance(32)
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFont("Cascadia Code", 12)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.highlighter = PythonHighlighter(self.editor.document())
        layout.addWidget(self.editor)

    def open_file(self, file_path):
        if not os.path.exists(file_path):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开文件失败: {e}")

    def set_content(self, content):
        self.editor.setPlainText(content)

    def get_content(self):
        return self.editor.toPlainText()

    def _new_file(self):
        self.editor.clear()
        self.current_file = None
        self.file_label.setText("[未命名]")

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开脚本", "", "Python 文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            self.open_file(file_path)

    def _save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.file_label.setText(os.path.basename(self.current_file))
                self.script_modified.emit(self.current_file)
                return True
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {e}")
        else:
            return self._save_as_file()
        return False

    def _save_as_file(self):
        default_dir = ""
        if self.current_file:
            default_dir = os.path.dirname(self.current_file)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存脚本", default_dir, "Python 文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            self.current_file = file_path
            return self._save_file()
        return False
