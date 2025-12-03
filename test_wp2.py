# v3.0.0 - Work Package 2: Verification Test
import sys
import os
from PyQt6.QtWidgets import QApplication
from lobby import LobbyWindow
from models import DebateState

def create_dummy_roles_if_missing():
    """Ensure we have roles to populate the list."""
    if not os.path.exists("roles"):
        os.makedirs("roles")
    
    roles = ["optimist", "pessimist", "stoic", "marxist", "capitalist"]
    for r in roles:
        path = f"roles/{r}.txt"
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Name: {r.capitalize()}\nYou are a {r}.")

def test_wp2():
    print("=== STARTING WP2 VERIFICATION ===")
    create_dummy_roles_if_missing()
    
    app = QApplication(sys.argv)
    
    # Create the Lobby
    lobby = LobbyWindow()
    
    # Connect the signal to a verifier function
    def on_debate_start(state: DebateState):
        print("\n[TEST SUCCESS] Signal received!")
        print(f"Topic: {state.topic}")
        print(f"Agents: {[a.name for a in state.agents]}")
        print("State JSON Preview:")
        print(state.to_json()[:200] + "...")
        
        # Close app after success
        print("Closing application...")
        lobby.close()
    
    lobby.debate_started.connect(on_debate_start)
    
    print("Launching Lobby Window...")
    print("INSTRUCTIONS FOR VERIFICATION:")
    print("1. Enter a Topic.")
    print("2. Add at least 2 agents from the left list.")
    print("3. Double click an agent in the right list to change their temperature.")
    print("4. Click 'Start Debate'.")
    
    lobby.show()
    app.exec()
    print("=== WP2 VERIFICATION FINISHED ===")

if __name__ == "__main__":
    test_wp2()
