import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QFileDialog, QDialogButtonBox, QLabel, QCheckBox,
    QGroupBox
)
from PySide6.QtCore import Qt


class RuleDialog(QDialog):
    def __init__(self, parent=None, rule=None, scripts_base_dir=""):
        super().__init__(parent)
        self.rule = rule
        self.scripts_base_dir = scripts_base_dir
        self.setWindowTitle("编辑规则" if rule else "添加规则")
        self.setMinimumWidth(550)
        self._setup_ui()
        if rule:
            self._load_rule(rule)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("我的 API 规则")
        form.addRow("名称:", self.name_edit)

        self.url_pattern_edit = QLineEdit()
        self.url_pattern_edit.setPlaceholderText(r"https://api\.example\.com/.*")
        form.addRow("URL 正则:", self.url_pattern_edit)

        self.enabled_check = QCheckBox("启用")
        self.enabled_check.setChecked(True)
        form.addRow("", self.enabled_check)

        layout.addLayout(form)

        script1_group = QGroupBox("代理1 脚本 (解密请求 / 加密响应)")
        s1_layout = QHBoxLayout()
        self.script1_edit = QLineEdit()
        self.script1_edit.setPlaceholderText("例如: my_api/decrypt.py")
        self.script1_edit.setReadOnly(True)
        s1_layout.addWidget(self.script1_edit)
        browse1_btn = QPushButton("浏览")
        browse1_btn.clicked.connect(lambda: self._browse_script("script1"))
        s1_layout.addWidget(browse1_btn)
        new1_btn = QPushButton("新建")
        new1_btn.clicked.connect(lambda: self._new_script("script1"))
        s1_layout.addWidget(new1_btn)
        script1_group.setLayout(s1_layout)
        layout.addWidget(script1_group)

        script2_group = QGroupBox("代理2 脚本 (加密请求 / 解密响应)")
        s2_layout = QHBoxLayout()
        self.script2_edit = QLineEdit()
        self.script2_edit.setPlaceholderText("例如: my_api/encrypt.py")
        self.script2_edit.setReadOnly(True)
        s2_layout.addWidget(self.script2_edit)
        browse2_btn = QPushButton("浏览")
        browse2_btn.clicked.connect(lambda: self._browse_script("script2"))
        s2_layout.addWidget(browse2_btn)
        new2_btn = QPushButton("新建")
        new2_btn.clicked.connect(lambda: self._new_script("script2"))
        s2_layout.addWidget(new2_btn)
        script2_group.setLayout(s2_layout)
        layout.addWidget(script2_group)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.Ok).setText("确定")
        btn_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(btn_box)

    def _to_rel(self, abs_path):
        if not abs_path:
            return ""
        scripts_dir = os.path.abspath(self.scripts_base_dir)
        abs_path = os.path.abspath(abs_path)
        try:
            return os.path.relpath(abs_path, scripts_dir)
        except ValueError:
            return abs_path

    def _browse_script(self, key):
        start_dir = self.scripts_base_dir or os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择脚本", start_dir, "Python 文件 (*.py);;所有文件 (*)"
        )
        if file_path:
            rel = self._to_rel(file_path)
            if key == "script1":
                self.script1_edit.setText(rel)
            else:
                self.script2_edit.setText(rel)

    def _new_script(self, key):
        start_dir = self.scripts_base_dir or os.getcwd()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "新建脚本", start_dir, "Python 文件 (*.py)"
        )
        if file_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            template = (
                '"""代理脚本"""\n'
                'from mitmproxy import ctx\n\n'
                'def request(flow):\n'
                '    ctx.log.info(f"[命中规则] 请求: {flow.request.pretty_url}")\n\n'
                'def response(flow):\n'
                '    ctx.log.info(f"[命中规则] 响应: {flow.response.status_code}")\n'
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)
            rel = self._to_rel(file_path)
            if key == "script1":
                self.script1_edit.setText(rel)
            else:
                self.script2_edit.setText(rel)

    def _load_rule(self, rule):
        self.name_edit.setText(rule.name)
        self.url_pattern_edit.setText(rule.url_pattern)
        self.enabled_check.setChecked(rule.enabled)
        self.script1_edit.setText(rule.script_proxy1)
        self.script2_edit.setText(rule.script_proxy2)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        url_pattern = self.url_pattern_edit.text().strip()
        if not name:
            return
        if not url_pattern:
            return
        self.accept()

    def get_rule_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "url_pattern": self.url_pattern_edit.text().strip(),
            "enabled": self.enabled_check.isChecked(),
            "script_proxy1": self.script1_edit.text(),
            "script_proxy2": self.script2_edit.text(),
        }
