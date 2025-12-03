# Multi-Agent Debate System v3.0

A sophisticated, native desktop application for orchestrating role-playing debates between AI agents. This system transitions from a linear CLI script to an event-driven PyQt6 application featuring a Director-Driven Simulation engine.

## Overview

The system allows users to compose a "Party" of specialized AI agents (e.g., The Stoic, The Futurist), define a debate topic, and watch them interact in real-time. The user acts as the "Director," capable of pausing the simulation and injecting instructions with varying degrees of influence—from subtle suggestions to critical system overrides.

## Technical Stack

*   **Language**: Python 3.10+
*   **GUI Framework**: PyQt6 (Native Widgets)
*   **State Management**: Pydantic
*   **API Integration**: OpenRouter (via OpenAI Python Client)
*   **Concurrency**: QThread / QRunnable

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/playa77/MADS
    cd MADS
    ```

2.  **Install dependencies**
    ```bash
    pip install PyQt6 pydantic python-dotenv openai
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory containing your OpenRouter API key:
    ```ini
    OPENROUTER_API_KEY=sk-or-v1-your-key-here
    ```

## Usage

1.  **Launch the Application**
    ```bash
    python3 app.py
    ```
    
2.  **The Lobby (Setup Phase)**
    *   **Topic**: Enter the resolution or question for the debate.
    *   **Library**: Drag agent roles from the left panel to the "Active Party" on the right.
    *   **Configuration**: Double-click any agent in the Active Party to customize their Display Name, Model (e.g., google/gemini-2.5-flash-lite), and Temperature.

3.  **The Arena (Runtime Phase)**
    *   **Start**: Click "Start Debate" to initialize the session.
    *   **Observation**: Agents will take turns debating. A visual progress bar indicates when an agent is querying the API.
    *   **Controls**: Use the "Pause/Resume" button to halt execution.

4.  **Director Mode (Intervention)**
    *   **Slider**: Adjust the "Influence Weight" (0.0 to 1.0).
        *   **0.0 - 0.3 (Subtle)**: Contextual note or suggestion.
        *   **0.4 - 0.7 (Mandatory)**: Required argument point.
        *   **0.8 - 1.0 (Override)**: Critical system directive; overrides previous logic.
    *   **Inject**: Type your instruction and click "INJECT". The engine will pause, insert the message, and force the next agent to react immediately.

## Architecture

The application follows a strict Model-View-Controller (MVC) pattern:

*   **Models (`models.py`)**: Defines `DebateState`, `AgentConfig`, and `Message` using Pydantic for strict typing and JSON serialization.
*   **View (`lobby.py`, `main_window.py`, `director.py`)**: PyQt6 widgets handling user interaction and rendering.
*   **Controller (`controller.py`)**: Manages application flow, bridges the Engine and UI, and handles API worker threads.
*   **Engine (`engine.py`)**: Headless state machine managing the turn queue and history.
*   **Workers (`workers.py`)**: Handles asynchronous communication with OpenRouter to prevent UI freezing.
*   **Role Manager (`role_manager.py`)**: Loads text-based agent templates from the `roles/` directory.

## Customization

To add new agent personalities, create a `.txt` file in the `roles/` directory. The filename becomes the ID, and the content serves as the System Prompt.

Example: `roles/skeptic.txt`
```text
Name: Skeptic
You are a radical skeptic. You question the premise of every argument presented to you.
```

## License

MIT License
