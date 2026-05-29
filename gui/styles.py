DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected {
    background-color: #45475a;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item:selected {
    background-color: #45475a;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 16px;
    font-weight: bold;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}
QTableWidget {
    background-color: #181825;
    alternate-background-color: #1e1e2e;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 4px;
    selection-background-color: #45475a;
    color: #cdd6f4;
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background-color: #11111b;
    color: #89b4fa;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #313244;
    font-weight: bold;
}
QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #585b70;
}
QPushButton:pressed {
    background-color: #6c7086;
}
QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}
QPushButton#startBtn {
    background-color: #40a02b;
    border-color: #40a02b;
}
QPushButton#startBtn:hover {
    background-color: #4caf50;
}
QPushButton#stopBtn {
    background-color: #d20f39;
    border-color: #d20f39;
}
QPushButton#stopBtn:hover {
    background-color: #e64553;
}
QLineEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #45475a;
}
QLineEdit:focus {
    border-color: #89b4fa;
}
QTextEdit, QPlainTextEdit {
    background-color: #11111b;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    selection-background-color: #45475a;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
    height: 2px;
}
QStatusBar {
    background-color: #11111b;
    color: #a6adc8;
    border-top: 1px solid #313244;
}
QLabel {
    color: #cdd6f4;
}
QComboBox {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #89b4fa;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #313244;
}
QCheckBox {
    color: #cdd6f4;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #45475a;
    border-radius: 3px;
    background-color: #181825;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    border: 1px solid #313244;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
}
QScrollBar:vertical {
    background-color: #181825;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #181825;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 6px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    spacing: 4px;
}
QSpinBox {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
