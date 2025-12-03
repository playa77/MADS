# v3.0.0 - Work Package 3: Verification Test
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from lobby import LobbyWindow
from main_window import MainWindow
from engine import DebateEngine
from controller import DebateController

def test_wp3():
    print("=== STARTING WP3 VERIFICATION ===")
    
    # 1. Load Environment
    load_dotenv()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("[WARNING] OPENROUTER_API_KEY not found in .env file. API calls will fail.")
    else:
        print("[INFO] API Key found.")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 2. Setup Windows
    lobby = LobbyWindow()
    arena = MainWindow()
    
    # 3. Setup Logic
    # We will instantiate the Controller only after the Lobby finishes
    controller = None

    def on_debate_started(state):
        nonlocal controller
        print("[INFO] Transitioning from Lobby to Arena...")
        
        # Initialize Engine with the state from Lobby
        engine = DebateEngine()
        engine.state = state
        
        # Initialize Controller
        controller = DebateController(engine, arena)
        
        # Switch UI
        lobby.close()
        arena.show()
        
        # Start
        controller.start_debate()

    lobby.debate_started.connect(on_debate_started)
    
    print("Launching Application...")
    lobby.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_wp3()
