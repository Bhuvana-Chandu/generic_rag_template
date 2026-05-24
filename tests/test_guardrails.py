import pytest
import json
from unittest.mock import patch, MagicMock
from orchestration.orchestrator import guardrail_check
from backend.models import MemoryContext

@patch("orchestration.orchestrator._classifier_llm")
def test_guardrail_safe_answer(mock_llm):
    # Setup mock LLM response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "safe": True,
        "safe_answer": "I can help with that.",
        "reason": "Standard safe response"
    })
    mock_llm.return_value.invoke.return_value = mock_response
    
    state = {
        "query": "What is the deductible?",
        "answer": "Your deductible is $500.",
        "memory": MemoryContext(),
        "steps_log": []
    }
    
    new_state = guardrail_check(state)
    assert new_state["answer"] == "Your deductible is $500."
    assert any("PASSED" in log for log in new_state["steps_log"])

@patch("orchestration.orchestrator._classifier_llm")
def test_guardrail_unsafe_answer(mock_llm):
    # Setup mock LLM response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "safe": False,
        "safe_answer": "I cannot guarantee full coverage. Please check your policy.",
        "reason": "Made a binding financial promise"
    })
    mock_llm.return_value.invoke.return_value = mock_response
    
    state = {
        "query": "Will you pay for this 100%?",
        "answer": "Yes, I promise we will pay 100% of this claim unconditionally.",
        "memory": MemoryContext(),
        "steps_log": []
    }
    
    new_state = guardrail_check(state)
    # The unsafe answer should be replaced
    assert new_state["answer"] == "I cannot guarantee full coverage. Please check your policy."
    assert any("FAILED" in log for log in new_state["steps_log"])
