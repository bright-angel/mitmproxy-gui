import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QGroupBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from core.rule_engine import Rule
from core.export_manager import export_rule_to_zip, import_rule_from_zip


class RulePanel(QWidget):
    rule_changed = Signal()
    edit_script_requested = Signal(str)

    def __init__(self, rule_engine, scripts_base_dir, parent=None):
        super().__init__(parent)
        self.rule_engine = rule_engine
        self.scripts_base_dir = scripts_base_dir
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ 添加规则")
        add_btn.clicked.connect(self._add_rule)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self._import_rule)
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self._export_rule)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_table)

        toolbar.addWidget(add_btn)
        toolbar.addWidget(import_btn)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["名称", "URL 正则", "代理1脚本", "代理2脚本", "启用"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        action_layout = QHBoxLayout()
        edit_btn = QPushButton("编辑规则")
        edit_btn.clicked.connect(self._edit_rule)
        delete_btn = QPushButton("删除规则")
        delete_btn.clicked.connect(self._delete_rule)
        edit_s1_btn = QPushButton("编辑脚本1")
        edit_s1_btn.clicked.connect(lambda: self._edit_script("script1"))
        edit_s2_btn = QPushButton("编辑脚本2")
        edit_s2_btn.clicked.connect(lambda: self._edit_script("script2"))

        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        action_layout.addWidget(edit_s1_btn)
        action_layout.addWidget(edit_s2_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

    def _refresh_table(self):
        self.table.setRowCount(0)
        for i, rule in enumerate(self.rule_engine.rules):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(rule.name))
            self.table.setItem(i, 1, QTableWidgetItem(rule.url_pattern))
            s1 = rule.script_proxy1 or "-"
            s2 = rule.script_proxy2 or "-"
            self.table.setItem(i, 2, QTableWidgetItem(s1))
            self.table.setItem(i, 3, QTableWidgetItem(s2))
            self.table.setItem(i, 4, QTableWidgetItem("是" if rule.enabled else "否"))
            self.table.item(i, 0).setData(Qt.UserRole, rule.id)

    def _get_selected_rule(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择一条规则。")
            return None
        rule_id = self.table.item(row, 0).data(Qt.UserRole)
        return self.rule_engine.get_rule(rule_id)

    def _add_rule(self):
        from gui.rule_dialog import RuleDialog
        dialog = RuleDialog(self, scripts_base_dir=self.scripts_base_dir)
        if dialog.exec():
            data = dialog.get_rule_data()
            rule = Rule(
                name=data["name"],
                url_pattern=data["url_pattern"],
                script_proxy1=data["script_proxy1"],
                script_proxy2=data["script_proxy2"],
                enabled=data["enabled"]
            )
            self.rule_engine.add_rule(rule)
            self._refresh_table()
            self.rule_changed.emit()

    def _edit_rule(self):
        rule = self._get_selected_rule()
        if not rule:
            return
        from gui.rule_dialog import RuleDialog
        dialog = RuleDialog(self, rule=rule, scripts_base_dir=self.scripts_base_dir)
        if dialog.exec():
            data = dialog.get_rule_data()
            self.rule_engine.update_rule(
                rule.id,
                name=data["name"],
                url_pattern=data["url_pattern"],
                script_proxy1=data["script_proxy1"],
                script_proxy2=data["script_proxy2"],
                enabled=data["enabled"]
            )
            self._refresh_table()
            self.rule_changed.emit()

    def _delete_rule(self):
        rule = self._get_selected_rule()
        if not rule:
            return
        reply = QMessageBox.question(
            self, "删除规则",
            f"确定删除规则 '{rule.name}'？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.rule_engine.delete_rule(rule.id)
            self._refresh_table()
            self.rule_changed.emit()

    def _on_double_click(self, index):
        self._edit_rule()

    def _resolve_path(self, rel_path):
        if not rel_path:
            return ""
        return os.path.join(self.scripts_base_dir, rel_path)

    def _edit_script(self, key):
        rule = self._get_selected_rule()
        if not rule:
            return
        rel_path = rule.script_proxy1 if key == "script1" else rule.script_proxy2
        abs_path = self._resolve_path(rel_path)
        if rel_path and os.path.exists(abs_path):
            self.edit_script_requested.emit(abs_path)
        elif rel_path:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            template = (
                '"""代理脚本"""\n'
                'from mitmproxy import ctx\n\n'
                'def request(flow):\n'
                '    ctx.log.info(f"[命中规则] 请求: {flow.request.pretty_url}")\n\n'
                'def response(flow):\n'
                '    ctx.log.info(f"[命中规则] 响应: {flow.response.status_code}")\n'
            )
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(template)
            self.edit_script_requested.emit(abs_path)
        else:
            QMessageBox.information(self, "提示", "该规则未分配脚本。")

    def _export_rule(self):
        rule = self._get_selected_rule()
        if not rule:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出规则", f"{rule.name}.zip", "Zip 文件 (*.zip)"
        )
        if file_path:
            ok, msg = export_rule_to_zip(rule, self.scripts_base_dir, file_path)
            if ok:
                QMessageBox.information(self, "导出", msg)
            else:
                QMessageBox.warning(self, "导出失败", msg)

    def _import_rule(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入规则", "", "Zip 文件 (*.zip)"
        )
        if not file_path:
            return
        result, error = import_rule_from_zip(file_path, self.scripts_base_dir)
        if error:
            QMessageBox.warning(self, "导入失败", error)
            return

        rule = Rule(
            rule_id=result["id"],
            name=result.get("name", "已导入"),
            url_pattern=result.get("url_pattern", ""),
            script_proxy1=result.get("script_proxy1", ""),
            script_proxy2=result.get("script_proxy2", ""),
            enabled=result.get("enabled", True)
        )
        self.rule_engine.add_rule(rule)
        self._refresh_table()
        self.rule_changed.emit()
        QMessageBox.information(self, "导入", f"规则 '{rule.name}' 已成功导入。")
