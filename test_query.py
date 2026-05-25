import sys
import os
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.tools import preload_tools
from backend.session_manager import manager

def run_test():
    # Preload the tools (this is the step we added to main.py!)
    preload_tools()
    
    # Get a fresh orchestrator session
    orch = manager.get_orchestrator("test_session_123")
    
    query = "Can you give me the phone numbers for all the approved plumbing and heating contractors near the SW1 postcode?"
    print(f"User Query: {query}\n")
    
    # Run the query
    result = orch.ask_detailed(query)
    
    print("\n" + "="*50)
    print("FINAL AI ANSWER:")
    print("="*50)
    print(result["answer"])
    
    print("\n" + "="*50)
    print("STEPS LOG:")
    print("="*50)
    for step in result["steps_log"]:
        print(step)

if __name__ == "__main__":
    run_test()
