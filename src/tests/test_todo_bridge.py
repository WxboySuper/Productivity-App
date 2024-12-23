import unittest
from unittest.mock import Mock, patch
from src.python.todo_bridge import handle_command

class TestTodoBridgeHandleCommand(unittest.TestCase):
    """Test suite for handle_command function in todo_bridge.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_todo = Mock()
        patcher = patch('src.python.todo_bridge.todo', self.mock_todo)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_tasks_command(self):
        """Test handle_command with get_tasks command"""
        # Setup mock return value
        test_tasks = [(1, "Test task")]
        self.mock_todo.tasks = test_tasks

        # Execute test
        result = handle_command("get_tasks", {})

        # Verify results
        self.assertEqual(result, test_tasks)

    def test_add_tasks_command(self):
        """Test handle_command with add_tasks command"""
        # Setup test data
        test_payload = {
            "title": "New Task",
            "deadline": "2024-01-01",
            "category": "Test"
        }

        # Execute test
        handle_command("add_tasks", test_payload)

        # Verify add_task was called with correct parameters
        self.mock_todo.add_task.assert_called_once_with(
            test_payload["title"],
            test_payload["deadline"],
            test_payload["category"]
        )

    def test_invalid_command(self):
        """Test handle_command with invalid command"""
        # Execute test & verify
        result = handle_command("invalid_command", {})
        self.assertIsNone(result)

    def test_add_tasks_with_missing_payload(self):
        """Test add_tasks command with missing payload fields"""
        # Setup test data with missing fields
        incomplete_payload = {
            "title": "New Task"
        }

        # Execute test
        with self.assertRaises(KeyError):
            handle_command("add_tasks", incomplete_payload)

    def test_command_with_empty_payload(self):
        """Test handle_command with empty payload"""
        # Execute test for get_tasks (should work with empty payload)
        result = handle_command("get_tasks", {})
        self.assertEqual(result, self.mock_todo.tasks)
