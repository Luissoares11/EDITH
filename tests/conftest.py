import pytest
from pathlib import Path

# We import the modules that hold state we need to isolate
import memory.store
import intent.llm

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Creates a fresh, temporary SQLite database for every test.
    Automatically patches memory.store.DB_PATH to use it.
    """
    temp_db = tmp_path / "test_edith.db"
    monkeypatch.setattr(memory.store, "DB_PATH", temp_db)
    
    # Initialize the tables in the temporary database
    memory.store.init_db()
    
    yield temp_db

@pytest.fixture
def mock_llm(monkeypatch):
    """
    Allows tests to easily mock Claude's response so we don't 
    waste API credits or wait for network calls during unit testing.
    """
    def _set_mock_response(action_dict):
        def _mock_interpret(*args, **kwargs):
            return action_dict
        monkeypatch.setattr(intent.llm, "interpret_with_llm", _mock_interpret)
    return _set_mock_response