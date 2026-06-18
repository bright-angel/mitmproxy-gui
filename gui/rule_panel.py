import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QAbstractItemView, QStyle
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from core.rule_engine import Rule
from core.export_manager import export_rule_to_zip, import_rule_from_zip


class RulePanel(QWidget):
    rule_changed = Signal()
    edit_script_requested = Signal(str)

    def __init__(self, rule_engine, parent=None):
        super().__init__(parent)
        self.rule_engine = rule_engine
        self._setup_ui()
        self._refresh_table()

    @property
    def rules_dir(self):
        return self.rule_engine.get_rules_dir()

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
            ["名称", "URL 正则", "代理1", "代理2", "操作"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 290)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

    def _refresh_table(self):
        self.table.setRowCount(0)
        for i, rule in enumerate(self.rule_engine.rules):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 36)

            name_item = QTableWidgetItem(rule.name)
            name_item.setData(Qt.UserRole, rule.id)
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, QTableWidgetItem(rule.url_pattern))

            p1_item = QTableWidgetItem("✓ 启用" if rule.proxy1_enabled else "✗ 禁用")
            p1_item.setForeground(Qt.green if rule.proxy1_enabled else Qt.gray)
            self.table.setItem(i, 2, p1_item)

            p2_item = QTableWidgetItem("✓ 启用" if rule.proxy2_enabled else "✗ 禁用")
            p2_item.setForeground(Qt.green if rule.proxy2_enabled else Qt.gray)
            self.table.setItem(i, 3, p2_item)

            # Inline action buttons
            self.table.setCellWidget(i, 4, self._create_action_widget(rule.id))

    def _create_action_widget(self, rule_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        def make_btn(text, color, callback):
            btn = QPushButton(text)
            btn.setFixedSize(48, 26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #cdd6f4;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {color}cc;
                }}
            """)
            btn.clicked.connect(callback)
            return btn

        edit_btn = make_btn("编辑", "#45475a", lambda checked=False, rid=rule_id: self._edit_rule_by_id(rid))
        s1_btn = make_btn("脚本1", "#1e66f5", lambda checked=False, rid=rule_id: self._edit_script_by_id(rid, "proxy1"))
        s2_btn = make_btn("脚本2", "#40a02b", lambda checked=False, rid=rule_id: self._edit_script_by_id(rid, "proxy2"))
        del_btn = make_btn("删除", "#d20f39", lambda checked=False, rid=rule_id: self._delete_rule_by_id(rid))

        layout.addWidget(edit_btn)
        layout.addWidget(s1_btn)
        layout.addWidget(s2_btn)
        layout.addWidget(del_btn)
        return widget

    # ── inline button handlers ──────────────────────────────

    def _edit_rule_by_id(self, rule_id):
        rule = self.rule_engine.get_rule(rule_id)
        if not rule:
            return
        from gui.rule_dialog import RuleDialog
        dialog = RuleDialog(self, rule=rule)
        if dialog.exec():
            data = dialog.get_rule_data()
            self.rule_engine.update_rule(
                rule.id,
                name=data["name"],
                url_pattern=data["url_pattern"],
                proxy1_enabled=data["proxy1_enabled"],
                proxy2_enabled=data["proxy2_enabled"],
            )
            self._refresh_table()
            self.rule_changed.emit()

    def _edit_script_by_id(self, rule_id, proxy_key):
        rule = self.rule_engine.get_rule(rule_id)
        if not rule:
            return
        self._open_script(rule, proxy_key)

    def _delete_rule_by_id(self, rule_id):
        rule = self.rule_engine.get_rule(rule_id)
        if not rule:
            return
        reply = QMessageBox.question(
            self, "删除规则",
            f"确定删除规则 '{rule.name}'？\n此操作将删除整个规则目录。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.rule_engine.delete_rule(rule.id)
            self._refresh_table()
            self.rule_changed.emit()

    # ── legacy selection-based handlers ─────────────────────

    def _get_selected_rule(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        rule_id = self.table.item(row, 0).data(Qt.UserRole)
        return self.rule_engine.get_rule(rule_id)

    def _add_rule(self):
        from gui.rule_dialog import RuleDialog
        dialog = RuleDialog(self)
        if dialog.exec():
            data = dialog.get_rule_data()
            rule = Rule(
                name=data["name"],
                url_pattern=data["url_pattern"],
                proxy1_enabled=data["proxy1_enabled"],
                proxy2_enabled=data["proxy2_enabled"],
            )
            self.rule_engine.add_rule(rule)
            self._refresh_table()
            self.rule_changed.emit()

    def _edit_rule(self):
        """Kept for double-click compatibility — delegates to selected rule."""
        rule = self._get_selected_rule()
        if not rule:
            QMessageBox.information(self, "提示", "请先选择一条规则。")
            return
        self._edit_rule_by_id(rule.id)

    def _delete_rule(self):
        rule = self._get_selected_rule()
        if not rule:
            QMessageBox.information(self, "提示", "请先选择一条规则。")
            return
        self._delete_rule_by_id(rule.id)

    def _on_double_click(self, index):
        row = index.row()
        rule_id = self.table.item(row, 0).data(Qt.UserRole)
        if rule_id:
            self._edit_rule_by_id(rule_id)

    def _edit_script(self, proxy_key):
        rule = self._get_selected_rule()
        if not rule:
            return
        self._open_script(rule, proxy_key)

    def _open_script(self, rule, proxy_key):
        script_path = self.rule_engine.get_rule_script_path(rule.id, proxy_key)

        if not os.path.exists(script_path):
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            label = "代理1" if proxy_key == "proxy1" else "代理2"
            template = (
                f'"""代理脚本 — {rule.name} ({label})"""\n'
                'from mitmproxy import ctx\n\n'
                'def request(flow):\n'
                f'    ctx.log.info("[{rule.name}] 请求: {{flow.request.method}} {{flow.request.pretty_url}}")\n\n'
                'def response(flow):\n'
                f'    ctx.log.info("[{rule.name}] 响应: {{flow.response.status_code}} {{flow.request.pretty_url}}")\n'
            )
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(template)

        self.edit_script_requested.emit(script_path)

    # ── import / export ─────────────────────────────────────

    def _export_rule(self):
        rule = self._get_selected_rule()
        if not rule:
            QMessageBox.information(self, "提示", "请先选择一条规则。")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出规则", f"{rule.name}.zip", "Zip 文件 (*.zip)"
        )
        if file_path:
            ok, msg = export_rule_to_zip(rule, self.rules_dir, file_path)
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
        result, error = import_rule_from_zip(file_path, self.rules_dir)
        if error:
            QMessageBox.warning(self, "导入失败", error)
            return

        self.rule_engine.load()
        self._refresh_table()
        self.rule_changed.emit()
        QMessageBox.information(self, "导入", f"规则已成功导入至 '{result.get('id', '')}'。")
