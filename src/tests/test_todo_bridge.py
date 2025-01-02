import unittest
from unittest.mock import Mock, patch
from python.todo_bridge import handle_command

class TestTodoBridgeHandleCommand(unittest.TestCase):
    """Test suite for handle_command function in todo_bridge.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_todo = Mock()
        # Fix the patch path to match the actual import in todo_bridge.py
        patcher = patch('python.todo_bridge.todo', self.mock_todo)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_tasks_command(self):
        """Test handle_command with get_tasks command"""
        # Setup mock return value with full task structure
        test_tasks = [(1, "Test task", None, None, None, None, None, None)]
        # Configure the tasks property mock
        type(self.mock_todo).tasks = property(lambda self: test_tasks)

        # Execute test
        result = handle_command("get_tasks", {})

        # Verify results
        self.assertEqual(result, test_tasks)

    def test_add_task_command(self):  # Renamed from test_add_tasks_command
        """Test handle_command with add_task command"""
        # Setup test data
        test_payload = {
            "title": "New Task",
            "deadline": "2024-01-01",
            "category": "Test"
        }

        # Execute test
        handle_command("add_task", test_payload)  # Changed from add_tasks to add_task

        # Verify add_task was called with correct parameters
        self.mock_todo.add_task.assert_called_once_with(
            test_payload["title"],
            test_payload["deadline"],
            test_payload["category"]
        )

    def test_invalid_command(self):
        """Test handle_command with invalid command"""
        with self.assertRaises(ValueError) as context:
            handle_command("invalid_command", {})
        self.assertEqual(str(context.exception), "Unknown command: invalid_command")

    def test_add_task_with_missing_payload(self):  # Renamed to match command name
        """Test add_task command with invalid payload"""
        # Test cases for invalid payloads
        invalid_payloads = [
            {},  # Empty payload
            {"title": ""},  # Empty title
            {"title": None},  # None title
            {"something": "else"}  # Missing title
        ]

        for payload in invalid_payloads:
            with self.assertRaises(ValueError) as context:
                handle_command("add_task", payload)
            self.assertEqual(
                str(context.exception),
                "Missing required fields in payload"
            )

    def test_command_with_empty_payload(self):
        """Test handle_command with empty payload"""
        # Setup mock tasks property with a list
        test_tasks = [(1, "Test task", None, None, None, None, None, None)]
        type(self.mock_todo).tasks = property(lambda self: test_tasks)

        # Execute test for get_tasks (should work with empty payload)
        result = handle_command("get_tasks", {})
        self.assertEqual(result, test_tasks)
