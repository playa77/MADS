# v3.0.0 - Work Package 4: Director UI Component
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, 
    QTextEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class DirectorPanel(QWidget):
    """
    UI for the Director Mode.
    Emits 'injection_requested(content, weight)' when the user acts.
    """
    injection_requested = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Container Frame
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #f0f3f4;
                border-top: 2px solid #bdc3c7;
                border-radius: 5px;
            }
        """)
        frame_layout = QVBoxLayout()

        # Header
        lbl_title = QLabel("Director Mode (Intervention)")
        lbl_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        frame_layout.addWidget(lbl_title)

        # Slider Section
        slider_layout = QHBoxLayout()
        self.lbl_weight = QLabel("Influence: 0.0 (Subtle)")
        self.lbl_weight.setFixedWidth(150)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100) # 0.00 to 1.00
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_change)
        
        slider_layout.addWidget(self.lbl_weight)
        slider_layout.addWidget(self.slider)
        frame_layout.addLayout(slider_layout)

        # Input Section
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Enter your intervention message here...")
        self.input_field.setMaximumHeight(60)
        
        self.btn_inject = QPushButton("INJECT")
        self.btn_inject.setMinimumHeight(60)
        self.btn_inject.setMinimumWidth(100)
        self.btn_inject.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_inject.clicked.connect(self.on_inject)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_inject)
        frame_layout.addLayout(input_layout)

        self.frame.setLayout(frame_layout)
        layout.addWidget(self.frame)
        self.setLayout(layout)

    def on_slider_change(self, value):
        weight = value / 100.0
        
        # Update Label
        if weight <= 0.3:
            desc = "Subtle"
            color = "#3498db" # Blue
        elif weight <= 0.7:
            desc = "Mandatory"
            color = "#9b59b6" # Purple
        else:
            desc = "OVERRIDE"
            color = "#c0392b" # Red

        self.lbl_weight.setText(f"Influence: {weight:.2f} ({desc})")
        
        # Update Button Color
        self.btn_inject.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)

    def on_inject(self):
        content = self.input_field.toPlainText().strip()
        if not content:
            return
        
        weight = self.slider.value() / 100.0
        self.injection_requested.emit(content, weight)
        self.input_field.clear()
