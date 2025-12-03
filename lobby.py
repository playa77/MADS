# v3.0.1 - Work Package 2: The Lobby UI (Updated Model List)
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QPlainTextEdit, QSplitter, QMessageBox,
    QListWidgetItem, QDialog, QFormLayout, QComboBox, QDoubleSpinBox,
    QLineEdit, QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal

from models import AgentConfig, DebateState
from role_manager import RoleManager

class AgentConfigDialog(QDialog):
    def __init__(self, config: AgentConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"Configure {config.name}")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit(self.config.name)
        layout.addRow("Display Name:", self.name_edit)

        self.model_combo = QComboBox()
        # UPDATED MODEL LIST - Development Priority
        models = [
            "google/gemini-2.5-flash-lite",
            "x-ai/grok-4.1-fast:free",
            "z-ai/glm-4.5-air:free",
            "nousresearch/hermes-3-llama-3.1-405b:free"
        ]
        self.model_combo.addItems(models)
        self.model_combo.setEditable(True)
        
        index = self.model_combo.findText(self.config.model_name)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            self.model_combo.setCurrentText(self.config.model_name)
            
        layout.addRow("Model:", self.model_combo)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(self.config.temperature)
        layout.addRow("Temperature:", self.temp_spin)

        self.prompt_preview = QPlainTextEdit(self.config.system_prompt)
        self.prompt_preview.setMaximumHeight(100)
        layout.addRow("System Prompt:", self.prompt_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_updated_config(self) -> AgentConfig:
        self.config.name = self.name_edit.text()
        self.config.model_name = self.model_combo.currentText()
        self.config.temperature = self.temp_spin.value()
        self.config.system_prompt = self.prompt_preview.toPlainText()
        return self.config

class LobbyWindow(QWidget):
    debate_started = pyqtSignal(object) 

    def __init__(self):
        super().__init__()
        self.role_manager = RoleManager()
        self.party_configs = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Multi-Agent Debate Platform v3.0 - Lobby")
        self.resize(1000, 700)
        
        main_layout = QVBoxLayout()
        
        topic_group = QWidget()
        topic_layout = QVBoxLayout()
        topic_layout.setContentsMargins(0, 0, 0, 0)
        lbl_topic = QLabel("<b>Debate Topic:</b>")
        self.topic_input = QPlainTextEdit()
        self.topic_input.setPlaceholderText("Enter the resolution or question for the debate...")
        self.topic_input.setMaximumHeight(80)
        topic_layout.addWidget(lbl_topic)
        topic_layout.addWidget(self.topic_input)
        topic_group.setLayout(topic_layout)
        main_layout.addWidget(topic_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("<b>Available Roles</b> (Drag to Party)"))
        
        self.library_list = QListWidget()
        self.library_list.setDragEnabled(True)
        self.library_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.populate_library()
        
        left_layout.addWidget(self.library_list)
        left_widget.setLayout(left_layout)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_add = QPushButton("Add >>")
        self.btn_add.clicked.connect(self.add_selected_agent)
        self.btn_remove = QPushButton("<< Remove")
        self.btn_remove.clicked.connect(self.remove_selected_agent)
        
        controls_layout.addWidget(self.btn_add)
        controls_layout.addWidget(self.btn_remove)
        controls_widget.setLayout(controls_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Active Party</b> (Double-click to Configure)"))
        
        self.party_list = QListWidget()
        self.party_list.setAcceptDrops(True)
        self.party_list.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.party_list.itemDoubleClicked.connect(self.open_config_dialog)
        
        right_layout.addWidget(self.party_list)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(controls_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 100, 400])
        
        main_layout.addWidget(splitter, stretch=1)

        footer_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Debate")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #2ecc71; color: white;")
        self.btn_start.clicked.connect(self.on_start_click)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_start)
        
        main_layout.addLayout(footer_layout)
        
        self.setLayout(main_layout)

    def populate_library(self):
        roles = self.role_manager.list_available_roles()
        self.library_list.clear()
        for role in roles:
            item = QListWidgetItem(role)
            self.library_list.addItem(item)

    def add_selected_agent(self):
        items = self.library_list.selectedItems()
        if not items:
            return
        
        role_id = items[0].text()
        self._add_agent_to_party(role_id)

    def _add_agent_to_party(self, role_id: str):
        config = self.role_manager.load_role(role_id)
        if not config:
            QMessageBox.warning(self, "Error", f"Could not load role: {role_id}")
            return

        existing_ids = [c.id for c in self.party_configs]
        original_id = config.id
        counter = 1
        while config.id in existing_ids:
            config.id = f"{original_id}_{counter}"
            counter += 1
        
        self.party_configs.append(config)
        
        item_text = f"{config.name} ({config.model_name})"
        item = QListWidgetItem(item_text)
        self.party_list.addItem(item)

    def remove_selected_agent(self):
        row = self.party_list.currentRow()
        if row < 0:
            return
        
        self.party_list.takeItem(row)
        self.party_configs.pop(row)

    def open_config_dialog(self, item):
        row = self.party_list.row(item)
        config = self.party_configs[row]
        
        dlg = AgentConfigDialog(config, self)
        if dlg.exec():
            updated_config = dlg.get_updated_config()
            self.party_configs[row] = updated_config
            item.setText(f"{updated_config.name} ({updated_config.model_name})")

    def on_start_click(self):
        topic = self.topic_input.toPlainText().strip()
        
        if not topic:
            QMessageBox.warning(self, "Validation Error", "Please enter a debate topic.")
            return
        
        if len(self.party_configs) < 2:
            QMessageBox.warning(self, "Validation Error", "You need at least 2 agents to start a debate.")
            return

        try:
            state = DebateState(
                topic=topic,
                agents=self.party_configs,
                status="IDLE"
            )
            self.debate_started.emit(state)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize debate: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LobbyWindow()
    window.show()
    sys.exit(app.exec())
