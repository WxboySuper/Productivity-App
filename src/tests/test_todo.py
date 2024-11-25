from src.python.todo import TodoList

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

class TestTodoList(unittest.TestCase):
    """Test suite for TodoList class functionality."""

    # Test data constants
    BASIC_TASK = "Test task"
    TASK_IDS = {
        'BASIC': 1,
        'FULL': 2,
        'PARTIAL': 3,
        'SUCCESS_MSG': 4,
        'REFRESH': 5
    }

    FULL_TASK_DATA = {
        'title': "Complete project",
        'category': "Work",
        'notes': "Important project",
        'priority': 1
    }

    PARTIAL_TASK_DATA = {
        'title': "Buy groceries",
        'category': "Personal",
        'priority': 2
    }

    SUCCESS_MESSAGE = "Task 'Test task' added successfully!"

    def setUp(self):
        """Initialize TodoList with mock database."""
        self.mock_db = Mock()
        self.todo_list = TodoList(db=self.mock_db)

    def test_add_task_basic(self):
        """Verify basic task creation with minimal parameters."""
        self.mock_db.add_task.return_value = self.TASK_IDS['BASIC']
        task_id = self.todo_list.add_task(self.BASIC_TASK)
        self.mock_db.add_task.assert_called_once_with(self.BASIC_TASK, None, None, None, None)
        self.assertEqual(task_id, self.TASK_IDS['BASIC'])

    def test_add_task_with_all_parameters(self):
        """Verify task creation with all available parameters."""
        self.mock_db.add_task.return_value = self.TASK_IDS['FULL']
        deadline = datetime.now()
        task_data = self.FULL_TASK_DATA.copy()
        
        task_id = self.todo_list.add_task(
            task_data['title'],
            deadline=deadline,
            category=task_data['category'],
            notes=task_data['notes'],
            priority=task_data['priority']
        )
        
        self.mock_db.add_task.assert_called_once_with(
            task_data['title'],
            deadline,
            task_data['category'],
            task_data['notes'],
            task_data['priority']
        )
        self.assertEqual(task_id, self.TASK_IDS['FULL'])

    def test_add_task_with_partial_parameters(self):
        """Verify task creation with partial parameters."""
        self.mock_db.add_task.return_value = self.TASK_IDS['PARTIAL']
        task_data = self.PARTIAL_TASK_DATA
        
        task_id = self.todo_list.add_task(
            task_data['title'],
            category=task_data['category'],
            priority=task_data['priority']
        )
        
        self.mock_db.add_task.assert_called_once_with(
            task_data['title'],
            None,
            task_data['category'],
            None,
            task_data['priority']
        )
        self.assertEqual(task_id, self.TASK_IDS['PARTIAL'])

    @patch('builtins.print')
    def test_add_task_success_message(self, mock_print):
        """Verify success message is printed after task creation."""
        self.mock_db.add_task.return_value = self.TASK_IDS['SUCCESS_MSG']
        self.todo_list.add_task(self.BASIC_TASK)
        mock_print.assert_called_once_with(self.SUCCESS_MESSAGE)

    def test_add_task_refresh_called(self):
        """Verify task list is refreshed after adding a task."""
        self.mock_db.add_task.return_value = self.TASK_IDS['REFRESH']
        self.todo_list.refresh_tasks = Mock()
        self.todo_list.add_task(self.BASIC_TASK)
        self.todo_list.refresh_tasks.assert_called_once()
