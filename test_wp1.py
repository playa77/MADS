# v3.0.0 - Work Package 1: Verification Test
import os
import time
from models import Message
from role_manager import RoleManager
from engine import DebateEngine

def create_dummy_roles():
    """Create dummy role files for testing if they don't exist."""
    if not os.path.exists("roles"):
        os.makedirs("roles")
    
    roles = {
        "optimist": "Name: Optimist\nYou are an optimist. Always look on the bright side.",
        "pessimist": "Name: Pessimist\nYou are a pessimist. Everything is doomed."
    }
    
    for rid, content in roles.items():
        path = f"roles/{rid}.txt"
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[Test] Created dummy role: {path}")

def test_wp1():
    print("=== STARTING WP1 VERIFICATION ===")
    
    # 1. Setup Environment
    create_dummy_roles()
    
    # 2. Test Role Manager
    print("\n--- Testing RoleManager ---")
    rm = RoleManager()
    available = rm.list_available_roles()
    print(f"Available Roles: {available}")
    
    if not available:
        print("[Error] No roles found. Aborting.")
        return

    # Load two agents
    agent1 = rm.load_role("optimist")
    agent2 = rm.load_role("pessimist")
    
    if not agent1 or not agent2:
        print("[Error] Failed to load agents.")
        return
        
    print(f"Loaded Agent 1: {agent1.name} (ID: {agent1.id})")
    print(f"Loaded Agent 2: {agent2.name} (ID: {agent2.id})")

    # 3. Test Engine Initialization
    print("\n--- Testing DebateEngine Initialization ---")
    engine = DebateEngine()
    topic = "Is the glass half full or half empty?"
    engine.initialize_debate(topic, [agent1, agent2], max_rounds=2)
    
    assert engine.state.status == "IDLE"
    assert len(engine.state.agents) == 2
    assert engine.state.topic == topic
    print("Engine initialized successfully.")

    # 4. Test State Machine & Turn Logic
    print("\n--- Testing State Machine & Loop ---")
    engine.start()
    assert engine.state.status == "RUNNING"
    
    # Simulate 4 turns (2 rounds)
    for i in range(4):
        current_agent = engine.get_current_agent()
        print(f"\nTurn {i+1}: It is {current_agent.name}'s turn.")
        
        # Mocking the LLM response generation
        mock_content = f"This is a simulated response from {current_agent.name} for turn {i+1}."
        
        # Create message object
        msg = Message(
            sender_id=current_agent.id,
            sender_name=current_agent.name,
            role="assistant",
            content=mock_content
        )
        
        # Append to history
        engine.append_message(msg)
        
        # Advance turn
        engine.advance_turn()
        
        # Verify history grew
        assert len(engine.state.history) == i + 1

    # 5. Test Completion
    print("\n--- Testing Completion ---")
    # We set max_rounds=2. After 4 turns (2 agents * 2 rounds), status should be COMPLETED.
    print(f"Current Status: {engine.state.status}")
    assert engine.state.status == "COMPLETED"
    
    # 6. Test Injection
    print("\n--- Testing Director Injection ---")
    engine.inject_message("Stop arguing!", weight=0.9)
    last_msg = engine.state.history[-1]
    assert last_msg.is_injection == True
    assert last_msg.influence_weight == 0.9
    assert last_msg.sender_name == "Director"
    
    # 7. Test Serialization
    print("\n--- Testing Serialization ---")
    save_path = "test_debate_state.json"
    engine.save_to_file(save_path)
    
    assert os.path.exists(save_path)
    
    # Create new engine and load
    new_engine = DebateEngine()
    new_engine.load_from_file(save_path)
    
    assert len(new_engine.state.history) == len(engine.state.history)
    assert new_engine.state.topic == engine.state.topic
    assert new_engine.state.agents[0].name == engine.state.agents[0].name
    
    print("Serialization/Deserialization successful.")
    
    # Cleanup
    if os.path.exists(save_path):
        os.remove(save_path)
        print(f"Removed test file: {save_path}")

    print("\n=== WP1 VERIFICATION COMPLETE: SUCCESS ===")

if __name__ == "__main__":
    try:
        test_wp1()
    except AssertionError as e:
        print(f"\n[FAILED] Assertion Error: {e}")
    except Exception as e:
        print(f"\n[FAILED] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
