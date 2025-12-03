# v3.0.0 - Work Package 4: Controller (Updated with Director & Delays)
import os
from PyQt6.QtCore import QObject, QThreadPool, QTimer
from PyQt6.QtWidgets import QMessageBox

from engine import DebateEngine
from models import DebateState, Message
from main_window import MainWindow
from workers import OpenRouterWorker
from prompt_engine import apply_influence_shader

class DebateController(QObject):
    """
    MVC Controller. Manages the flow between Engine, UI, and API Workers.
    """
    def __init__(self, engine: DebateEngine, main_window: MainWindow):
        super().__init__()
        self.engine = engine
        self.ui = main_window
        self.thread_pool = QThreadPool.globalInstance()
        self.is_waiting_delay = False # Lock to ensure delay respect
        
        # Connect UI signals
        self.ui.pause_requested.connect(self.on_pause)
        self.ui.resume_requested.connect(self.on_resume)
        self.ui.injection_requested.connect(self.on_injection)

    def start_debate(self):
        self.ui.set_topic(self.engine.state.topic)
        self.ui.append_system_message(f"Debate initialized with {len(self.engine.state.agents)} agents.")
        self.engine.start()
        self.trigger_next_turn()

    def on_pause(self):
        self.engine.pause()

    def on_resume(self):
        self.engine.resume()
        self.trigger_next_turn()

    def on_injection(self, content: str, weight: float):
        """
        Handle Director intervention.
        1. Pause engine (if running).
        2. Inject message into history.
        3. Resume engine.
        4. Trigger next turn immediately (agents react to injection).
        """
        print(f"[Controller] Injection received: {content} (Weight: {weight})")
        
        # 1. Inject into Engine
        self.engine.inject_message(content, weight)
        
        # 2. Update UI
        self.ui.append_message("Director", content, is_injection=True)
        
        # 3. Force Resume if paused, or just continue
        if self.engine.state.status == "PAUSED":
            self.ui.btn_pause.setChecked(False)
            self.ui.btn_pause.setText("Pause")
            self.ui.lbl_status.setText("Status: RUNNING")
            self.engine.resume()
        
        # 4. Trigger next turn (with small safety delay to clear UI events)
        # We do not wait the full 2s here because this is a user action
        QTimer.singleShot(500, self.trigger_next_turn)

    def trigger_next_turn(self):
        """
        Determines if we should proceed to the next turn and initiates it.
        """
        # Checks
        if self.engine.state.status != "RUNNING":
            return
        if self.is_waiting_delay:
            return # Still in the mandatory silence period

        agent = self.engine.get_current_agent()
        if not agent:
            return

        # Prepare Context
        messages = [{"role": "system", "content": agent.system_prompt}]
        
        # Get history
        transcript = self.engine.get_context_for_current_turn(history_limit=15)
        
        # Check for recent injections to highlight in prompt
        last_msg = self.engine.state.history[-1] if self.engine.state.history else None
        injection_instruction = ""
        if last_msg and last_msg.is_injection:
            # Apply the Influence Shader logic to the PROMPT sent to the agent
            # Note: The history already contains the raw message. 
            # We add a specific instruction here to ensure they obey the weight.
            injection_instruction = apply_influence_shader(last_msg.content, last_msg.influence_weight)
            print(f"[Controller] Applying Shader: {injection_instruction}")

        prompt_content = (
            f"The debate topic is: {self.engine.state.topic}\n\n"
            f"Recent transcript:\n{transcript}\n\n"
            f"{injection_instruction}\n\n"
            f"It is now your turn. Respond as {agent.name}. "
            f"Keep it concise (under 200 words). React to the previous speaker."
        )
        
        messages.append({"role": "user", "content": prompt_content})

        # UI Update
        self.ui.set_thinking(True, agent.name)

        # Launch Worker
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.ui.append_system_message("ERROR: OPENROUTER_API_KEY not found.")
            self.ui.set_thinking(False)
            return

        worker = OpenRouterWorker(
            api_key=api_key,
            model_name=agent.model_name,
            messages=messages,
            temperature=agent.temperature
        )
        
        worker.signals.result.connect(lambda content: self.handle_turn_complete(agent, content))
        worker.signals.error.connect(self.handle_error)
        
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

        # 4. Schedule next turn with MANDATORY DELAY
        # We set a lock so no other turns can trigger
        self.is_waiting_delay = True
        
        delay_ms = 2500 # 2.5 seconds (meeting the >2s requirement)
        print(f"[Controller] Turn complete. Waiting {delay_ms}ms before next turn...")
        
        def release_lock_and_trigger():
            self.is_waiting_delay = False
            self.trigger_next_turn()

        QTimer.singleShot(delay_ms, release_lock_and_trigger)

    def handle_error(self, error_msg):
        self.ui.set_thinking(False)
        self.ui.append_system_message(f"API Error: {error_msg}")
        self.engine.pause()
        self.ui.btn_pause.setChecked(True)
        self.ui.btn_pause.setText("Resume")
        self.ui.lbl_status.setText("Status: PAUSED (Error)")
