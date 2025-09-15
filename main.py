#!/usr/bin/env python3
"""
Orchestrator for the multi-agent debate system.

Key changes:
- Graceful Ctrl+C handling (signal).
- Interactive by default (--interactive default True).
- Configurable delay between model calls (config + CLI --delay).
- Full reply printed (no truncation).
- Sanitization call assumed present in utils.sanitize_reply.
"""

import argparse
import json
import os
import time
import datetime
import signal
import threading
from typing import List
from pathlib import Path
from rich.console import Console
from rich.progress import track

from agents import Agent, load_prompt_from_file, create_model_for_agent, format_debate_transcript
from utils import prune_history, safe_append_json, exponential_backoff, sanitize_reply

from langchain.schema import SystemMessage, HumanMessage

console = Console()
_shutdown_event = threading.Event()

# Register termination signals for graceful shutdown
def _signal_handler(signum, frame):
    console.print(f"[yellow]Received signal {signum} — shutting down gracefully...[/yellow]")
    _shutdown_event.set()

signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, _signal_handler)  # docker stop


def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_agents(cfg: dict) -> List[Agent]:
    agents_cfg = cfg.get('agents', [])
    agents = []
    for a in agents_cfg:
        prompt = ''
        if 'system_prompt_file' in a and a['system_prompt_file']:
            prompt = load_prompt_from_file(a['system_prompt_file'])
        elif 'system_prompt' in a:
            prompt = a['system_prompt']
        else:
            prompt = f"You are {a.get('name','Agent')}. Stay in role, respond concisely in 2–4 paragraphs, use plain language, and when you propose a speculative strategic outcome, label it clearly as speculation. Do NOT output chain-of-thought, internal reasoning steps, or meta-level thinking markers. Provide only the response text that should be shown to users."
        agent = Agent(id=a['id'], name=a.get('name', a['id']), system_prompt=prompt)
        agents.append(agent)
    return agents


def compose_prompt(history: List[dict], agent: Agent) -> str:
    transcript = format_debate_transcript(history)
    instruction = (
        f"The debate so far (most recent first):\n{transcript}\n\n"
        f"You are responding *as* {agent.name}. Reply in character. "
        f"Focus on advancing the discussion: critique the last speaker, add one concrete suggestion, "
        "and (optionally) request clarification if something is ambiguous. Label speculation clearly."
    )
    return instruction


def delay_with_countdown(seconds: float):
    """Sleep with a visible countdown in the terminal."""
    if seconds <= 0:
        return
    for i in range(int(seconds), 0, -1):
        console.print(f"[cyan]Waiting {i} second(s) before next model call...[/cyan]", end='\r')
        time.sleep(1)
    console.print(" " * 60, end='\r')  # clear the line


def run_debate(cfg_path: str, max_rounds: int = None, interactive: bool = True, delay: float | None = None):
    cfg = load_config(cfg_path)
    agents = build_agents(cfg)

    # Create Chat model objects per agent
    models = {}
    for agent in agents:
        models[agent.id] = create_model_for_agent(cfg, agent)

    history = []  # list of utterances: {sender, content, ts}
    log_file = cfg.get('logging', {}).get('file', 'data/debates.json')
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    rounds_total = max_rounds or cfg.get('conversation', {}).get('rounds', 50)
    history_window = cfg.get('conversation', {}).get('history_window_utts', 12)
    stop_on_repeat = cfg.get('conversation', {}).get('stop_on_repeat', 2)
    # default delay: CLI > config > 5s
    cfg_default_delay = cfg.get('conversation', {}).get('query_delay_seconds', 5)
    delay = delay if delay is not None else cfg_default_delay

    # seed topic if provided
    seed = cfg.get('conversation', {}).get('seed_topic')
    if seed:
        history.append({
            'sender': 'User',
            'content': seed,
            'ts': datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    console.print(f"Starting debate: {len(agents)} agents, up to {rounds_total} rounds. Interactive={interactive}, delay={delay}s")

    for r in range(rounds_total):
        if _shutdown_event.is_set():
            console.print("[yellow]Shutdown requested — exiting main loop.[/yellow]")
            break

        console.print(f"--- Round {r+1}/{rounds_total} ---")
        for agent in agents:
            if _shutdown_event.is_set():
                console.print("[yellow]Shutdown requested — aborting current round.[/yellow]")
                break

            pruned = prune_history(history, history_window)
            human_prompt = compose_prompt(list(reversed(pruned)), agent) if pruned else (
                f"You are {agent.name}. Start the debate on the seeded topic."
            )

            sys_msg = SystemMessage(content=agent.system_prompt)
            human_msg = HumanMessage(content=human_prompt)

            model = models[agent.id]

            # Special-case: if an agent with id 'user' exists, ask for input instead of calling the LLM.
            if agent.id == 'user':
                console.print("[bold green]Your turn (type your message, blank to skip):[/bold green]")
                try:
                    user_msg = input().strip()
                except EOFError:
                    user_msg = ''
                reply_text = user_msg or "(user skipped)"
            else:
                def call_model():
                    return model([sys_msg, human_msg])

                try:
                    resp_msg = exponential_backoff(call_model, exceptions=(Exception,), max_tries=3)
                except Exception as e:
                    console.print(f"[red]Model error for agent {agent.id}: {e}[/red]")
                    # still log failure event
                    safe_append_json(log_file, {
                        'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'round': r + 1,
                        'agent_id': agent.id,
                        'agent_name': agent.name,
                        'content': f"<ERROR: {e}>",
                        'model': getattr(model, 'model', None),
                    })
                    continue

                reply_text = getattr(resp_msg, 'content', str(resp_msg) )

                # Sanitize (remove thought leaks / role prefixes)
                reply_text = sanitize_reply(reply_text)

            # Log the full turn (untruncated)
            turn_obj = {
                'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'round': r + 1,
                'agent_id': agent.id,
                'agent_name': agent.name,
                'content': reply_text,
                'model': getattr(model, 'model', None),
            }
            safe_append_json(log_file, turn_obj)

            # Print the full reply to terminal (no truncation)
            console.print(f"[bold]{agent.name}:[/bold]\n{reply_text}\n")

            # Update history
            history.append({'sender': agent.name, 'content': reply_text, 'ts': turn_obj['ts']})

            # stopping rule: fuzzy similarity (if enabled)
            if stop_on_repeat and stop_on_repeat > 0:
                from difflib import SequenceMatcher
                def similar(a: str, b: str) -> float:
                    return SequenceMatcher(None, a, b).ratio()
                threshold = cfg.get('conversation', {}).get('repeat_similarity_threshold', 0.88)
                recent = history[-(stop_on_repeat+1):-1] if len(history) >= stop_on_repeat+1 else []
                similar_count = sum(1 for h in recent if similar(h['content'].strip(), reply_text.strip()) >= threshold)
                if similar_count >= stop_on_repeat:
                    console.print(f"[yellow]Stopping: {agent.name} repeated a similar answer {similar_count} times (threshold {threshold}).[/yellow]")
                    _shutdown_event.set()
                    break

            # Interactive user insertion (Option A). pause for input if interactive
            if interactive:
                console.print("Press Enter to continue, type 'u:your message' to inject a User message, or 'q' to quit:")
                try:
                    user_in = input().strip()
                except EOFError:
                    user_in = ''
                if user_in.lower() == 'q':
                    console.print("User requested stop — exiting.")
                    _shutdown_event.set()
                    break
                if user_in.startswith('u:') or user_in.startswith('U:'):
                    user_msg = user_in.split(':', 1)[1].strip()
                    if user_msg:
                        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        history.append({'sender': 'User', 'content': user_msg, 'ts': ts})
                        safe_append_json(log_file, {'ts': ts, 'round': r+1, 'agent_id': 'user', 'agent_name': 'User', 'content': user_msg, 'model': None})

            # Respect delay between model queries to be polite to API provider
            if delay and delay > 0:
                delay_with_countdown(delay)
                # allow immediate exit on shutdown event while sleeping (sleep in small increments)
#                slept = 0.0
#                while slept < delay:
#                    if _shutdown_event.is_set():
#                        break
                    

        if _shutdown_event.is_set():
            break

    console.print("Debate finished or interrupted. Logs appended to " + log_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Multi-agent debate runner (LangChain + OpenRouter).")
    parser.add_argument('--config', default='config.json', help='Path to config.json')
    parser.add_argument('--rounds', type=int, default=None, help='Override rounds in config')
    parser.add_argument('--interactive', action='store_true', default=True, help='Run in interactive mode (default: True). Use --no-interactive to disable.')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false', help='Disable interactive prompts.')
    parser.add_argument('--delay', type=float, default=None, help='Seconds delay between model calls (overrides config).')
    args = parser.parse_args()

    run_debate(cfg_path=args.config, max_rounds=args.rounds, interactive=args.interactive, delay=args.delay)
