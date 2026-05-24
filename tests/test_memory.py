import pytest
import json
from unittest.mock import patch, MagicMock
from backend.session_manager import SessionManager

@patch("backend.session_manager.redis.Redis.from_url")
def test_session_manager_init(mock_redis):
    # Setup mock
    mock_client = MagicMock()
    mock_redis.return_value = mock_client
    
    # Test init
    manager = SessionManager()
    assert manager.redis_client is not None
    mock_client.ping.assert_called_once()

@patch("backend.session_manager.redis.Redis.from_url")
def test_save_and_get_chat_history(mock_redis):
    # Setup mock Redis to behave like a dict
    mock_client = MagicMock()
    storage = {}
    
    def mock_setex(name, time, value):
        storage[name] = value
        
    def mock_get(name):
        return storage.get(name)
        
    mock_client.setex.side_effect = mock_setex
    mock_client.get.side_effect = mock_get
    mock_redis.return_value = mock_client
    
    manager = SessionManager()
    
    # Test save
    session_id = "test-session-123"
    fake_history = [("user", "hello"), ("ai", "hi")]
    manager.save_chat_history(session_id, fake_history)
    
    # Verify save
    assert f"session:{session_id}:history" in storage
    
    # Test get
    retrieved = manager.get_chat_history(session_id)
    assert len(retrieved) == 2
    assert retrieved[0] == ["user", "hello"]  # JSON converts tuple to list
