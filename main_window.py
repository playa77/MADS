# v3.0.0 - Work Package 3: Main Arena Window
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class MainWindow(QWidget):
    """
    The runtime arena. Displays the chat and controls.
    """
    # Signals for the Controller to hook into
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Multi-Agent Debate Platform v3.0 - Arena")
        self.resize(1200, 800)
        
        layout = QVBoxLayout()
        
        # 1. Header (Topic)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("background-color: #2c3e50; color: white; padding: 10px;")
        header_layout = QVBoxLayout()
        self.lbl_topic = QLabel("Topic: ...")
        self.lbl_topic.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_topic.setWordWrap(True)
        header_layout.addWidget(self.lbl_topic)
        self.header_frame.setLayout(header_layout)
        layout.addWidget(self.header_frame)

        # 2. Chat View
        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(False)
        self.chat_view.setStyleSheet("""
            QTextBrowser {
                background-color: #ecf0f1;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.chat_view)

        # 3. Status Bar / Controls
        status_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("Status: IDLE")
        self.lbl_status.setStyleSheet("font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(200)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause)

        status_layout.addWidget(self.lbl_status)
        status_layout.addWidget(self.progress_bar)
        status_layout.addStretch()
        status_layout.addWidget(self.btn_pause)
        
        layout.addLayout(status_layout)
        self.setLayout(layout)

    def set_topic(self, topic: str):
        self.lbl_topic.setText(f"Topic: {topic}")

    def append_message(self, sender: str, content: str, is_user: bool = False):
        """
        Formats and appends a message to the chat view.
        """
        color = "#2980b9" if is_user else "#2c3e50"
        bg_color = "#d4e6f1" if is_user else "#ffffff"
        align = "right" if is_user else "left"
        
        html = f"""
        <div style="margin-bottom: 15px; text-align: {align};">
            <div style="display: inline-block; background-color: {bg_color}; 
                        border: 1px solid #bdc3c7; border-radius: 8px; padding: 10px; max-width: 80%;">
                <b style="color: {color};">{sender}</b><br/>
                <span style="color: #333;">{content.replace(chr(10), '<br>')}</span>
            </div>
        </div>
        """
        self.chat_view.append(html)
        # Auto-scroll
        sb = self.chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def append_system_message(self, content: str):
        html = f"""
        <div style="text-align: center; margin: 10px; color: #7f8c8d;">
            <i>{content}</i>
        </div>
        """
        self.chat_view.append(html)

    def set_thinking(self, is_thinking: bool, agent_name: str = ""):
        self.progress_bar.setVisible(is_thinking)
        if is_thinking:
            self.lbl_status.setText(f"Status: {agent_name} is thinking...")
        else:
            self.lbl_status.setText("Status: Waiting")

    def toggle_pause(self):
        if self.btn_pause.isChecked():
            self.btn_pause.setText("Resume")
            self.pause_requested.emit()
            self.lbl_status.setText("Status: PAUSED")
        else:
            self.btn_pause.setText("Pause")
            self.resume_requested.emit()
            self.lbl_status.setText("Status: RUNNING")
