# v3.0.0 - Work Package 3: Controller
import os
from PyQt6.QtCore import QObject, QThreadPool
from PyQt6.QtWidgets import QMessageBox

from engine import DebateEngine
from models import DebateState, Message
from main_window import MainWindow
from workers import OpenRouterWorker

class DebateController(QObject):
    """
    MVC Controller. Manages the flow between Engine, UI, and API Workers.
    """
    def __init__(self, engine: DebateEngine, main_window: MainWindow):
        super().__init__()
        self.engine = engine
        self.ui = main_window
        self.thread_pool = QThreadPool.globalInstance()
        
        # Connect UI signals
        self.ui.pause_requested.connect(self.on_pause)
        self.ui.resume_requested.connect(self.on_resume)

    def start_debate(self):
        """
        Called when the debate is handed over from Lobby to Arena.
        """
        self.ui.set_topic(self.engine.state.topic)
        self.ui.append_system_message(f"Debate initialized with {len(self.engine.state.agents)} agents.")
        self.engine.start()
        self.trigger_next_turn()

    def on_pause(self):
        self.engine.pause()

    def on_resume(self):
        self.engine.resume()
        self.trigger_next_turn()

    def trigger_next_turn(self):
        """
        Determines if we should proceed to the next turn and initiates it.
        """
        if self.engine.state.status != "RUNNING":
            return

        agent = self.engine.get_current_agent()
        if not agent:
            return

        # Prepare Context
        # We construct the messages list for the LLM
        # System Prompt + History
        messages = [{"role": "system", "content": agent.system_prompt}]
        
        # Add debate history (pruned or full - for now full, but we should limit context window in real prod)
        # We convert our internal Message model to OpenAI format
        transcript = self.engine.get_context_for_current_turn(history_limit=15)
        
        # We wrap the transcript in a user message to prompt the agent
        prompt_content = (
            f"The debate topic is: {self.engine.state.topic}\n\n"
            f"Recent transcript:\n{transcript}\n\n"
            f"It is now your turn. Respond as {agent.name}. "
            f"Keep it concise (under 200 words). React to the previous speaker."
        )
        
        messages.append({"role": "user", "content": prompt_content})

        # UI Update
        self.ui.set_thinking(True, agent.name)

        # Launch Worker
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.ui.append_system_message("ERROR: OPENROUTER_API_KEY not found in environment.")
            self.ui.set_thinking(False)
            return

        worker = OpenRouterWorker(
            api_key=api_key,
            model_name=agent.model_name,
            messages=messages,
            temperature=agent.temperature
        )
        
        # Connect signals
        worker.signals.result.connect(lambda content: self.handle_turn_complete(agent, content))
        worker.signals.error.connect(self.handle_error)
        # We could hook up token_received to a temporary buffer in UI if we wanted real-time streaming text
        
        self.thread_pool.start(worker)

    def handle_turn_complete(self, agent, content):
        """
        Callback when LLM finishes generating.
        """
        self.ui.set_thinking(False)
        
        if self.engine.state.status != "RUNNING":
            return

        # 1. Update Model
        msg = Message(
            sender_id=agent.id,
            sender_name=agent.name,
            role="assistant",
            content=content
        )
        self.engine.append_message(msg)
        self.engine.advance_turn()

        # 2. Update UI
        self.ui.append_message(agent.name, content)

        # 3. Check for completion
        if self.engine.state.status == "COMPLETED":
            self.ui.append_system_message("Debate Completed (Max rounds reached).")
            return

        # 4. Schedule next turn (small delay for UX)
        # We use a QTimer in a real app, but here we just call directly or via simple delay
        # For safety in PyQt, we should use QTimer.singleShot
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, self.trigger_next_turn)

    def handle_error(self, error_msg):
        self.ui.set_thinking(False)
        self.ui.append_system_message(f"API Error: {error_msg}")
        # Pause on error so user can see it
        self.engine.pause()
        self.ui.btn_pause.setChecked(True)
        self.ui.btn_pause.setText("Resume")
        self.ui.lbl_status.setText("Status: PAUSED (Error)")
