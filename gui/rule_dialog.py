from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QCheckBox, QGroupBox
)


class RuleDialog(QDialog):
    def __init__(self, parent=None, rule=None):
        super().__init__(parent)
        self.rule = rule
        self.setWindowTitle("编辑规则" if rule else "添加规则")
        self.setMinimumWidth(500)
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

        layout.addLayout(form)

        # Proxy script enable toggles
        script_group = QGroupBox("脚本启用设置")
        script_layout = QVBoxLayout(script_group)

        self.proxy1_check = QCheckBox("启用 proxy1.py（代理1: 解密请求 / 加密响应）")
        self.proxy1_check.setChecked(True)
        script_layout.addWidget(self.proxy1_check)

        self.proxy2_check = QCheckBox("启用 proxy2.py（代理2: 加密请求 / 解密响应）")
        self.proxy2_check.setChecked(True)
        script_layout.addWidget(self.proxy2_check)

        note_label = QLabel(
            "每个规则固定包含 proxy1.py 和 proxy2.py 脚本文件。\n"
            "勾选对应的脚本即可在对应代理中生效。"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        script_layout.addWidget(note_label)

        layout.addWidget(script_group)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.Ok).setText("确定")
        btn_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(btn_box)

    def _load_rule(self, rule):
        self.name_edit.setText(rule.name)
        self.url_pattern_edit.setText(rule.url_pattern)
        self.proxy1_check.setChecked(rule.proxy1_enabled)
        self.proxy2_check.setChecked(rule.proxy2_enabled)

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
            "proxy1_enabled": self.proxy1_check.isChecked(),
            "proxy2_enabled": self.proxy2_check.isChecked(),
        }
