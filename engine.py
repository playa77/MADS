# v3.0.0 - Work Package 1: Debate Engine (Headless)
import datetime
from typing import List, Optional, Tuple
from models import DebateState, AgentConfig, Message

class DebateEngine:
    """
    The Model in the MVC pattern. 
    Manages the state machine, turn queue, and history.
    Does NOT contain UI code or Network calls.
    """
    def __init__(self):
        self.state = DebateState()
        print("[DebateEngine] Initialized in IDLE state.")

    def initialize_debate(self, topic: str, agents: List[AgentConfig], max_rounds: int = 10):
        """
        Sets up a new debate session.
        """
        try:
            self.state = DebateState(
                topic=topic,
                agents=agents,
                max_rounds=max_rounds,
                status="IDLE"
            )
            print(f"[DebateEngine] Debate initialized. Topic: '{topic}'. Agents: {len(agents)}")
        except Exception as e:
            print(f"[DebateEngine] Error initializing debate: {e}")
            raise

    def start(self):
        """Transitions state to RUNNING."""
        if not self.state.agents:
            raise ValueError("Cannot start debate with 0 agents.")
        
        self.state.status = "RUNNING"
        print("[DebateEngine] State transition: IDLE -> RUNNING")

    def pause(self):
        """Transitions state to PAUSED."""
        self.state.status = "PAUSED"
        print("[DebateEngine] State transition: -> PAUSED")

    def resume(self):
        """Transitions state to RUNNING."""
        self.state.status = "RUNNING"
        print("[DebateEngine] State transition: -> RUNNING")

    def get_current_agent(self) -> Optional[AgentConfig]:
        """Returns the agent whose turn it is."""
        if not self.state.agents:
            return None
        return self.state.agents[self.state.current_turn_index]

    def advance_turn(self):
        """
        Moves the turn index to the next agent.
        Increments round counter if we wrapped around.
        """
        if not self.state.agents:
            return

        next_index = (self.state.current_turn_index + 1) % len(self.state.agents)
        
        # Check if we completed a full round
        if next_index == 0:
            self.state.rounds_completed += 1
            print(f"[DebateEngine] Round {self.state.rounds_completed} completed.")

        self.state.current_turn_index = next_index
        
        # Check termination condition
        if self.state.rounds_completed >= self.state.max_rounds:
            self.state.status = "COMPLETED"
            print("[DebateEngine] Max rounds reached. Debate COMPLETED.")

    def append_message(self, message: Message):
        """
        Adds a message to history.
        """
        self.state.history.append(message)
        self.state.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[DebateEngine] Message appended from {message.sender_name}.")

    def inject_message(self, content: str, weight: float = 1.0):
        """
        Director Mode: Injects a message from the user/director.
        This does NOT advance the turn automatically; it inserts into history.
        """
        msg = Message(
            sender_id="director",
            sender_name="Director",
            role="user", # Treated as user input for the LLM
            content=content,
            influence_weight=weight,
            is_injection=True
        )
        self.append_message(msg)
        print(f"[DebateEngine] Injected message (Weight: {weight}): {content[:30]}...")

    def get_context_for_current_turn(self, history_limit: int = 10) -> str:
        """
        Generates the context string for the current agent.
        This is a helper for the prompt engine.
        """
        # Get recent history
        recent_msgs = self.state.history[-history_limit:] if len(self.state.history) > history_limit else self.state.history
        
        transcript = ""
        for msg in recent_msgs:
            transcript += f"{msg.sender_name}: {msg.content}\n\n"
            
        return transcript

    # Serialization wrappers
    def save_to_file(self, filepath: str):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.state.to_json())
            print(f"[DebateEngine] State saved to {filepath}")
        except Exception as e:
            print(f"[DebateEngine] Error saving state: {e}")

    def load_from_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            self.state = DebateState.from_json(json_str)
            print(f"[DebateEngine] State loaded from {filepath}")
        except Exception as e:
            print(f"[DebateEngine] Error loading state: {e}")
