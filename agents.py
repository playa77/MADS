#!/usr/bin/env python3
"""
agents.py

Defines Agent class and helper functions for creating LLMs for each debate participant.
Supports per-agent temperature, system prompts, and OpenRouter integration.
"""

import os
from pathlib import Path
from typing import Optional

# Attempt to import ChatOpenAI from langchain_openai or fallback to langchain.chat_models
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain.chat_models import ChatOpenAI
    except ImportError:
        raise ImportError(
            "Could not import ChatOpenAI from langchain_openai nor langchain.chat_models. "
            "Install 'langchain' and 'langchain-openai' packages."
        )


class Agent:
    """
    Represents a debate participant.
    """
    def __init__(self, id: str, name: str, system_prompt: str, temperature: Optional[float] = None):
        self.id = id
        self.name = name
        self.system_prompt = system_prompt
        self.temperature = temperature


def load_prompt_from_file(path: str) -> str:
    """
    Load a system prompt from a text file.
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"System prompt file not found: {path}")
    with p.open('r', encoding='utf-8') as f:
        return f.read().strip()


def create_model_for_agent(cfg: dict, agent: Agent):
    """
    Creates a ChatOpenAI model instance for a given agent.
    Supports per-agent temperature if specified; otherwise uses global model settings.
    """
    model_cfg = cfg.get('model', {})
    name = model_cfg.get('name', 'qwen/qwen3-30b-a3b:instruct')
    max_tokens = model_cfg.get('max_tokens', 512)
    # Per-agent temperature overrides global model setting
    temperature = agent.temperature if agent.temperature is not None else model_cfg.get('temperature', 0.6)

    # OpenRouter API integration
    openrouter_cfg = cfg.get('openrouter', {})
    api_env = openrouter_cfg.get('api_key_envvar', 'OPENROUTER_API_KEY')
    base_url = openrouter_cfg.get('base_url', 'https://openrouter.ai/api/v1')
    
    if not os.getenv(api_env):
        raise EnvironmentError(f"OpenRouter API key not found in environment variable {api_env}")

    try:
        # Try newer langchain parameter names first
        try:
            model = ChatOpenAI(
                model=name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=os.getenv(api_env),
                base_url=base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/your-project",
                    "X-Title": "Multi-Agent Debate System"
                }
            )
        except TypeError:
            # Fallback to older langchain parameter names
            model = ChatOpenAI(
                model_name=name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=os.getenv(api_env),
                openai_api_base=base_url
            )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize model for agent {agent.id}: {e}")
    return model


def format_debate_transcript(history: list[dict]) -> str:
    """
    Formats the debate history into a string for model input.
    Each turn: "AgentName: message"
    """
    lines = []
    for turn in history:
        sender = turn.get('sender', 'Unknown')
        content = turn.get('content', '').replace('\n', ' ')
        lines.append(f"{sender}: {content}")
    # Return most recent first if needed; main.py reverses history before passing
    return "\n".join(lines)
