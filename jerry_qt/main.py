#!/usr/bin/env python3
"""
JERRY - HITT Team Analysis Tool (PyQt6 Version)

Run: python jerry_qt/main.py
Build exe: pyinstaller --onefile --windowed jerry_qt/main.py
"""

import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QFileDialog, QLineEdit,
    QComboBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QListWidget,
    QSplitter, QFrame, QScrollArea, QMessageBox, QHeaderView,
    QProgressBar, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

# Import plotting
import pyqtgraph as pg


class DarkPalette(QPalette):
    """Dark theme color palette"""
    def __init__(self):
        super().__init__()

        # Base colors
        self.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
        self.setColor(QPalette.ColorRole.WindowText, QColor("#e2e8f0"))
        self.setColor(QPalette.ColorRole.Base, QColor("#16213e"))
        self.setColor(QPalette.ColorRole.AlternateBase, QColor("#1e2a4a"))
        self.setColor(QPalette.ColorRole.Text, QColor("#e2e8f0"))
        self.setColor(QPalette.ColorRole.Button, QColor("#16213e"))
        self.setColor(QPalette.ColorRole.ButtonText, QColor("#e2e8f0"))
        self.setColor(QPalette.ColorRole.BrightText, QColor("#00d4ff"))
        self.setColor(QPalette.ColorRole.Highlight, QColor("#ff6b35"))
        self.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setColor(QPalette.ColorRole.Link, QColor("#00d4ff"))


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e2e8f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QTabWidget::pane {
    border: none;
    background-color: #1a1a2e;
}

QTabBar::tab {
    background-color: #16213e;
    color: #94a3b8;
    padding: 12px 20px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #e2e8f0;
    border-bottom: 2px solid #ff6b35;
    font-weight: bold;
}

QTabBar::tab:hover {
    color: #e2e8f0;
    background-color: #1e2a4a;
}

QPushButton {
    background-color: #ff6b35;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #ff8c5a;
}

QPushButton:pressed {
    background-color: #e55a2b;
}

QPushButton:disabled {
    background-color: #555;
    color: #888;
}

QPushButton[secondary="true"] {
    background-color: #16213e;
    border: 1px solid #334155;
}

QPushButton[secondary="true"]:hover {
    background-color: #1e2a4a;
}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #0d1117;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 8px;
    color: #e2e8f0;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #00d4ff;
}

QComboBox {
    background-color: #0d1117;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 8px;
    color: #e2e8f0;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e2e8f0;
    selection-background-color: #ff6b35;
}

QGroupBox {
    background-color: #16213e;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 5px;
    color: #00d4ff;
}

QTableWidget {
    background-color: #0d1117;
    border: 1px solid #334155;
    gridline-color: #334155;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #ff6b35;
}

QHeaderView::section {
    background-color: #16213e;
    color: #e2e8f0;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #334155;
    font-weight: bold;
}

QListWidget {
    background-color: #0d1117;
    border: 1px solid #334155;
    border-radius: 4px;
}

QListWidget::item {
    padding: 8px;
}

QListWidget::item:selected {
    background-color: #ff6b35;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #334155;
    background-color: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #ff6b35;
    border-color: #ff6b35;
}

QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #334155;
    background-color: #0d1117;
}

QRadioButton::indicator:checked {
    background-color: #ff6b35;
    border-color: #ff6b35;
}

QScrollBar:vertical {
    background-color: #16213e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QProgressBar {
    background-color: #0d1117;
    border: 1px solid #334155;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #00d4ff;
    border-radius: 3px;
}

QLabel[heading="true"] {
    font-size: 18pt;
    font-weight: bold;
    color: #00d4ff;
}

QLabel[subheading="true"] {
    color: #94a3b8;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JERRY - HITT Team Analysis Tool")
        self.setMinimumSize(1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_tdms_tab(), "📁 TDMS CONVERSION")
        self.tabs.addTab(self._create_maxmin_tab(), "📐 MAXMIN CONVERTER")
        self.tabs.addTab(self._create_plot_tab(), "📊 PLOT DATA")
        self.tabs.addTab(self._create_avg_tab(), "📈 CYCLE AVERAGES")
        self.tabs.addTab(self._create_validation_tab(), "🔍 CYLINDERS VALIDATION")
        self.tabs.addTab(self._create_fuel_systems_tab(), "⛽ FUEL SYSTEMS")
        layout.addWidget(self.tabs)

        # State
        self.current_files = []
        self.current_columns = []

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet("background-color: #16213e; padding: 15px;")
        header.setFixedHeight(80)

        layout = QHBoxLayout(header)

        title = QLabel("JERRY")
        title.setStyleSheet("font-size: 32pt; font-weight: bold; color: #ff6b35;")
        layout.addWidget(title)

        subtitle = QLabel("HITT Team Analysis Tool")
        subtitle.setStyleSheet("font-size: 12pt; color: #004E89; margin-left: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(subtitle)

        layout.addStretch()

        return header

    def _create_scroll_area(self, widget):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _create_tdms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("TDMS Conversion")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("Convert TDMS files to cycle-separated text files")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("Select TDMS Files")
        file_layout = QHBoxLayout(file_group)

        self.tdms_btn = QPushButton("📂 Choose Files")
        self.tdms_btn.clicked.connect(self._tdms_choose_files)
        file_layout.addWidget(self.tdms_btn)

        self.tdms_label = QLabel("No files selected")
        self.tdms_label.setStyleSheet("color: #94a3b8;")
        file_layout.addWidget(self.tdms_label)
        file_layout.addStretch()

        layout.addWidget(file_group)

        # Options
        options_group = QGroupBox("Output Settings")
        options_layout = QFormLayout(options_group)

        self.tdms_delimiter = QComboBox()
        self.tdms_delimiter.addItems(["Tab", "Comma", "Semicolon"])
        options_layout.addRow("Delimiter:", self.tdms_delimiter)

        self.tdms_header = QCheckBox("Include column headers")
        self.tdms_header.setChecked(True)
        options_layout.addRow("", self.tdms_header)

        layout.addWidget(options_group)

        # Convert button
        convert_btn = QPushButton("▶ CONVERT FILES")
        convert_btn.clicked.connect(self._tdms_convert)
        layout.addWidget(convert_btn)

        layout.addStretch()

        return self._create_scroll_area(widget)

    def _create_maxmin_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("MaxMin Converter")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("Extract min/max values from multiple cycle files")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("Select Cycle Files")
        file_layout = QHBoxLayout(file_group)

        btn = QPushButton("📂 Choose Files")
        btn.clicked.connect(self._maxmin_choose_files)
        file_layout.addWidget(btn)

        self.maxmin_label = QLabel("No files selected")
        self.maxmin_label.setStyleSheet("color: #94a3b8;")
        file_layout.addWidget(self.maxmin_label)
        file_layout.addStretch()

        layout.addWidget(file_group)

        # Column selection
        col_group = QGroupBox("Columns to Analyze")
        col_layout = QVBoxLayout(col_group)

        self.maxmin_columns = QListWidget()
        self.maxmin_columns.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.maxmin_columns.setMaximumHeight(150)
        col_layout.addWidget(self.maxmin_columns)

        options = QHBoxLayout()
        self.maxmin_mean = QCheckBox("Include Mean")
        self.maxmin_mean.setChecked(True)
        options.addWidget(self.maxmin_mean)

        self.maxmin_std = QCheckBox("Include Std Dev")
        options.addWidget(self.maxmin_std)
        options.addStretch()
        col_layout.addLayout(options)

        layout.addWidget(col_group)

        # Extract button
        extract_btn = QPushButton("▶ EXTRACT MIN/MAX")
        extract_btn.clicked.connect(self._maxmin_extract)
        layout.addWidget(extract_btn)

        layout.addStretch()

        return self._create_scroll_area(widget)

    def _create_plot_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left panel - controls
        left = QWidget()
        left.setFixedWidth(350)
        left.setStyleSheet("background-color: #16213e;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Plot Configuration")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #00d4ff;")
        left_layout.addWidget(title)

        # File
        left_layout.addWidget(QLabel("Data File"))
        file_btn = QPushButton("📂 Choose File")
        file_btn.setProperty("secondary", True)
        file_btn.clicked.connect(self._plot_choose_file)
        left_layout.addWidget(file_btn)

        self.plot_file_label = QLabel("No file selected")
        self.plot_file_label.setStyleSheet("color: #94a3b8;")
        self.plot_file_label.setWordWrap(True)
        left_layout.addWidget(self.plot_file_label)

        # X axis
        left_layout.addWidget(QLabel("X-Axis (Cycle)"))
        self.plot_x = QComboBox()
        left_layout.addWidget(self.plot_x)

        # Y axis
        left_layout.addWidget(QLabel("Y-Axis Variable 1"))
        self.plot_y1 = QComboBox()
        left_layout.addWidget(self.plot_y1)

        left_layout.addWidget(QLabel("Y-Axis Variable 2"))
        self.plot_y2 = QComboBox()
        left_layout.addWidget(self.plot_y2)

        # Limits
        left_layout.addWidget(QLabel("Y-Axis Limits"))
        limits = QHBoxLayout()
        self.plot_ymin = QLineEdit()
        self.plot_ymin.setPlaceholderText("Min")
        limits.addWidget(self.plot_ymin)
        self.plot_ymax = QLineEdit()
        self.plot_ymax.setPlaceholderText("Max")
        limits.addWidget(self.plot_ymax)
        left_layout.addLayout(limits)

        # Title
        left_layout.addWidget(QLabel("Custom Title"))
        self.plot_title = QLineEdit()
        left_layout.addWidget(self.plot_title)

        left_layout.addStretch()

        # Buttons
        create_btn = QPushButton("▶ CREATE PLOT")
        create_btn.clicked.connect(self._plot_create)
        left_layout.addWidget(create_btn)

        export_btn = QPushButton("📷 Export Image")
        export_btn.setProperty("secondary", True)
        export_btn.clicked.connect(self._plot_export)
        left_layout.addWidget(export_btn)

        layout.addWidget(left)

        # Right panel - chart
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # PyQtGraph plot widget
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1a1a2e')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        right_layout.addWidget(self.plot_widget)

        layout.addWidget(right)

        return widget

    def _create_avg_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Cycle Averages & Statistics")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("Calculate averages, durations, and ramp rates across cycles")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("Select Cycle Files")
        file_layout = QHBoxLayout(file_group)

        btn = QPushButton("📂 Choose Files")
        btn.clicked.connect(self._avg_choose_files)
        file_layout.addWidget(btn)

        self.avg_label = QLabel("No files selected")
        self.avg_label.setStyleSheet("color: #94a3b8;")
        file_layout.addWidget(self.avg_label)
        file_layout.addStretch()

        layout.addWidget(file_group)

        # Config
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)

        self.avg_time_col = QComboBox()
        config_layout.addRow("Time Column:", self.avg_time_col)

        self.avg_time_mode = QComboBox()
        self.avg_time_mode.addItems(["Elapsed", "Time"])
        config_layout.addRow("Time Mode:", self.avg_time_mode)

        self.avg_ramp = QCheckBox("Compute Ptank ramp rate")
        self.avg_ramp.setChecked(True)
        config_layout.addRow("", self.avg_ramp)

        self.avg_ptank_col = QComboBox()
        config_layout.addRow("Ptank Column:", self.avg_ptank_col)

        layout.addWidget(config_group)

        # Compute button
        compute_btn = QPushButton("▶ COMPUTE STATISTICS")
        compute_btn.clicked.connect(self._avg_compute)
        layout.addWidget(compute_btn)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.avg_table = QTableWidget()
        self.avg_table.setMinimumHeight(200)
        results_layout.addWidget(self.avg_table)

        layout.addWidget(results_group)

        return self._create_scroll_area(widget)

    def _create_validation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Cylinders Validation")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("Validate cycle data against specification limits")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        # File selection
        file_group = QGroupBox("Select Data Files")
        file_layout = QHBoxLayout(file_group)

        btn = QPushButton("📂 Choose Files")
        btn.clicked.connect(self._val_choose_files)
        file_layout.addWidget(btn)

        self.val_label = QLabel("No files selected")
        self.val_label.setStyleSheet("color: #94a3b8;")
        file_layout.addWidget(self.val_label)
        file_layout.addStretch()

        layout.addWidget(file_group)

        # Limits table
        limits_group = QGroupBox("Parameter Limits")
        limits_layout = QVBoxLayout(limits_group)

        self.val_table = QTableWidget(0, 3)
        self.val_table.setHorizontalHeaderLabels(["Parameter", "Min", "Max"])
        self.val_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.val_table.setMinimumHeight(200)
        limits_layout.addWidget(self.val_table)

        layout.addWidget(limits_group)

        # Validate button
        validate_btn = QPushButton("▶ VALIDATE FILES")
        validate_btn.clicked.connect(self._val_validate)
        layout.addWidget(validate_btn)

        layout.addStretch()

        return self._create_scroll_area(widget)

    def _create_fuel_systems_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left panel - configuration
        left = QWidget()
        left.setFixedWidth(400)
        left.setStyleSheet("background-color: #16213e;")

        left_scroll = QScrollArea()
        left_scroll.setWidget(left)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(420)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)

        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Fuel Systems Validation")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #00d4ff;")
        left_layout.addWidget(title)

        # Files
        left_layout.addWidget(QLabel("Cycle Files"))
        file_btn = QPushButton("📂 Choose Files")
        file_btn.setProperty("secondary", True)
        file_btn.clicked.connect(self._fs_choose_files)
        left_layout.addWidget(file_btn)

        self.fs_files_label = QLabel("No files selected")
        self.fs_files_label.setStyleSheet("color: #94a3b8;")
        left_layout.addWidget(self.fs_files_label)

        # Column selection
        left_layout.addWidget(QLabel("Column Selection"))

        form = QFormLayout()
        self.fs_time_col = QComboBox()
        form.addRow("Time:", self.fs_time_col)

        self.fs_ptank_col = QComboBox()
        form.addRow("Ptank:", self.fs_ptank_col)

        self.fs_tfuel_col = QComboBox()
        form.addRow("tfuel:", self.fs_tfuel_col)

        self.fs_soc_col = QComboBox()
        form.addRow("SOC:", self.fs_soc_col)

        left_layout.addLayout(form)

        # Fill detection
        fill_group = QGroupBox("Fill Detection")
        fill_layout = QFormLayout(fill_group)

        self.fs_ptank_threshold = QDoubleSpinBox()
        self.fs_ptank_threshold.setValue(2.0)
        self.fs_ptank_threshold.setSingleStep(0.1)
        fill_layout.addRow("Ptank Threshold (MPa):", self.fs_ptank_threshold)

        end_mode = QHBoxLayout()
        self.fs_end_ptank = QRadioButton("Ptank")
        self.fs_end_ptank.setChecked(True)
        self.fs_end_soc = QRadioButton("SOC")
        end_mode.addWidget(self.fs_end_ptank)
        end_mode.addWidget(self.fs_end_soc)
        fill_layout.addRow("End of Fill:", end_mode)

        left_layout.addWidget(fill_group)

        # tfuel check
        tfuel_group = QGroupBox("tfuel Timing Check")
        tfuel_layout = QFormLayout(tfuel_group)

        self.fs_enable_tfuel = QCheckBox("Enable tfuel check")
        self.fs_enable_tfuel.setChecked(True)
        tfuel_layout.addRow("", self.fs_enable_tfuel)

        self.fs_tfuel_target = QDoubleSpinBox()
        self.fs_tfuel_target.setRange(-100, 100)
        self.fs_tfuel_target.setValue(-30)
        tfuel_layout.addRow("Target Temp (°C):", self.fs_tfuel_target)

        self.fs_tfuel_window = QDoubleSpinBox()
        self.fs_tfuel_window.setRange(0, 600)
        self.fs_tfuel_window.setValue(30)
        tfuel_layout.addRow("Time Window (s):", self.fs_tfuel_window)

        left_layout.addWidget(tfuel_group)

        # Ramp check
        ramp_group = QGroupBox("Ramp Rate Check")
        ramp_layout = QFormLayout(ramp_group)

        self.fs_enable_ramp = QCheckBox("Enable ramp check")
        ramp_layout.addRow("", self.fs_enable_ramp)

        self.fs_ramp_limit = QLineEdit()
        self.fs_ramp_limit.setPlaceholderText("Leave blank for report only")
        ramp_layout.addRow("Max (MPa/min):", self.fs_ramp_limit)

        left_layout.addWidget(ramp_group)

        left_layout.addStretch()

        # Buttons
        validate_btn = QPushButton("▶ VALIDATE FILES")
        validate_btn.clicked.connect(self._fs_validate)
        left_layout.addWidget(validate_btn)

        export_btn = QPushButton("📥 Export Results")
        export_btn.setProperty("secondary", True)
        export_btn.clicked.connect(self._fs_export)
        left_layout.addWidget(export_btn)

        layout.addWidget(left_scroll)

        # Right panel - results & chart
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # Results list
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)

        self.fs_results_list = QListWidget()
        self.fs_results_list.currentRowChanged.connect(self._fs_show_result)
        results_layout.addWidget(self.fs_results_list)

        right_layout.addWidget(results_group)

        # Chart
        chart_group = QGroupBox("Cycle Visualization")
        chart_layout = QVBoxLayout(chart_group)

        self.fs_plot = pg.PlotWidget()
        self.fs_plot.setBackground('#1a1a2e')
        self.fs_plot.showGrid(x=True, y=True, alpha=0.3)
        chart_layout.addWidget(self.fs_plot)

        right_layout.addWidget(chart_group)

        layout.addWidget(right)

        return widget

    # Event handlers
    def _tdms_choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select TDMS Files", "",
            "TDMS Files (*.tdms);;All Files (*.*)"
        )
        if files:
            self.current_files = files
            self.tdms_label.setText(f"✓ {len(files)} files selected")

    def _tdms_convert(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select TDMS files first.")
            return
        QMessageBox.information(self, "Info", "TDMS conversion coming soon.")

    def _maxmin_choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Cycle Files", "",
            "Data Files (*.txt *.csv *.dat *.log);;All Files (*.*)"
        )
        if files:
            self.current_files = files
            self.maxmin_label.setText(f"✓ {len(files)} files selected")
            self._load_columns(files[0], self.maxmin_columns)

    def _maxmin_extract(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select files first.")
            return
        QMessageBox.information(self, "Info", "MaxMin extraction coming soon.")

    def _plot_choose_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "",
            "Data Files (*.txt *.csv *.dat *.log);;All Files (*.*)"
        )
        if file:
            self.current_files = [file]
            self.plot_file_label.setText(os.path.basename(file))
            self._load_columns(file, self.plot_x)
            self._load_columns(file, self.plot_y1)
            self._load_columns(file, self.plot_y2)

    def _plot_create(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select a file first.")
            return
        QMessageBox.information(self, "Info", "Plot creation coming soon.")

    def _plot_export(self):
        QMessageBox.information(self, "Info", "Plot export coming soon.")

    def _avg_choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Cycle Files", "",
            "Data Files (*.txt *.csv *.dat *.log);;All Files (*.*)"
        )
        if files:
            self.current_files = files
            self.avg_label.setText(f"✓ {len(files)} files selected")
            self._load_columns(files[0], self.avg_time_col)
            self._load_columns(files[0], self.avg_ptank_col)

    def _avg_compute(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select files first.")
            return
        QMessageBox.information(self, "Info", "Statistics computation coming soon.")

    def _val_choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Data Files", "",
            "Data Files (*.txt *.csv *.dat *.log);;All Files (*.*)"
        )
        if files:
            self.current_files = files
            self.val_label.setText(f"✓ {len(files)} files selected")

    def _val_validate(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select files first.")
            return
        QMessageBox.information(self, "Info", "Validation coming soon.")

    def _fs_choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Cycle Files", "",
            "Data Files (*.txt *.csv *.dat *.log);;All Files (*.*)"
        )
        if files:
            self.current_files = files
            self.fs_files_label.setText(f"✓ {len(files)} files selected")
            self._load_columns(files[0], self.fs_time_col)
            self._load_columns(files[0], self.fs_ptank_col)
            self._load_columns(files[0], self.fs_tfuel_col)
            self._load_columns(files[0], self.fs_soc_col)

    def _fs_validate(self):
        if not self.current_files:
            QMessageBox.warning(self, "Error", "Please select files first.")
            return
        QMessageBox.information(self, "Info", "Fuel systems validation coming soon.")

    def _fs_export(self):
        QMessageBox.information(self, "Info", "Export coming soon.")

    def _fs_show_result(self, row):
        pass  # TODO: Show chart for selected result

    def _load_columns(self, filepath, combo_or_list):
        try:
            from powertech_tools.utils.file_parser import load_table_allow_duplicate_headers
            df = load_table_allow_duplicate_headers(filepath)
            columns = list(df.columns)

            if isinstance(combo_or_list, QComboBox):
                combo_or_list.clear()
                combo_or_list.addItems(columns)
            elif isinstance(combo_or_list, QListWidget):
                combo_or_list.clear()
                combo_or_list.addItems(columns)

            self.current_columns = columns
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read file: {e}")


def main():
    app = QApplication(sys.argv)

    # Apply dark theme
    app.setPalette(DarkPalette())
    app.setStyleSheet(DARK_STYLESHEET)

    # Set font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
