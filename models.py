# v3.0.0 - Work Package 1: Data Models
import datetime
from typing import List, Optional, Literal
from uuid import uuid4
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """
    Configuration for a single agent in the debate.
    """
    id: str = Field(..., description="Unique identifier for the agent (e.g., 'optimist')")
    name: str = Field(..., description="Display name of the agent")
    system_prompt: str = Field(..., description="The core personality instructions")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Creativity parameter")
    model_name: str = Field("deepseek/deepseek-chat", description="OpenRouter model string")
    
    # Visual/UI helper (optional for now, good for WP2)
    avatar_color: str = Field("#FFFFFF", description="Hex color code for UI")

class Message(BaseModel):
    """
    A single utterance in the debate history.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    sender_id: str = Field(..., description="ID of the agent or 'user'/'director'")
    sender_name: str = Field(..., description="Display name of the sender")
    role: Literal["system", "user", "assistant"] = Field(..., description="Role for LLM context")
    content: str = Field(..., description="The actual text content")
    
    # WP4: Influence Shader metadata
    influence_weight: float = Field(0.0, ge=0.0, le=1.0, description="Director influence level (0.0-1.0)")
    is_injection: bool = Field(False, description="True if injected by Director")

class DebateState(BaseModel):
    """
    The total serializable state of a debate session.
    """
    topic: str = Field("", description="The debate topic")
    agents: List[AgentConfig] = Field(default_factory=list, description="Active party members")
    history: List[Message] = Field(default_factory=list, description="Conversation log")
    
    # State Machine
    status: Literal["IDLE", "RUNNING", "PAUSED", "COMPLETED"] = Field("IDLE")
    current_turn_index: int = Field(0, description="Index of the agent whose turn it is")
    rounds_completed: int = Field(0)
    max_rounds: int = Field(50)
    
    last_updated: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_json(self) -> str:
        """Serialize state to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "DebateState":
        """Load state from JSON string."""
        return cls.model_validate_json(json_str)
