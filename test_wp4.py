# v3.0.0 - Work Package 4: Verification Test
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from lobby import LobbyWindow
from main_window import MainWindow
from engine import DebateEngine
from controller import DebateController

def test_wp4():
    print("=== STARTING WP4 VERIFICATION ===")
    
    load_dotenv()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("[WARNING] OPENROUTER_API_KEY not found.")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    lobby = LobbyWindow()
    arena = MainWindow()
    controller = None

    def on_debate_started(state):
        nonlocal controller
        print("[INFO] Transitioning to Arena with Director Mode...")
        
        engine = DebateEngine()
        engine.state = state
        
        controller = DebateController(engine, arena)
        
        lobby.close()
        arena.show()
        
        controller.start_debate()
        print("[INSTRUCTION] 1. Observe the 2.5s delay between turns.")
        print("[INSTRUCTION] 2. Use the slider at the bottom to set influence.")
        print("[INSTRUCTION] 3. Type a message and click INJECT.")
        print("[INSTRUCTION] 4. Verify the next agent responds to your injection.")

    lobby.debate_started.connect(on_debate_started)
    
    lobby.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_wp4()
