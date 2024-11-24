from ..todo import TodoList

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

class TestTodoList(unittest.TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.todo_list = TodoList(db=self.mock_db)

    def test_add_task_basic(self):
        self.mock_db.add_task.return_value = 1
        task_id = self.todo_list.add_task("Test task")
        self.mock_db.add_task.assert_called_once_with("Test task", None, None, None, None)
        self.assertEqual(task_id, 1)

    def test_add_task_with_all_parameters(self):
        self.mock_db.add_task.return_value = 2
        deadline = datetime.now()
        task_id = self.todo_list.add_task(
            "Complete project",
            deadline=deadline,
            category="Work",
            notes="Important project",
            priority=1
        )
        self.mock_db.add_task.assert_called_once_with(
            "Complete project",
            deadline,
            "Work",
            "Important project",
            1
        )
        self.assertEqual(task_id, 2)

    def test_add_task_with_partial_parameters(self):
        self.mock_db.add_task.return_value = 3
        task_id = self.todo_list.add_task(
            "Buy groceries",
            category="Personal",
            priority=2
        )
        self.mock_db.add_task.assert_called_once_with(
            "Buy groceries",
            None,
            "Personal",
            None,
            2
        )
        self.assertEqual(task_id, 3)

    @patch('builtins.print')
    def test_add_task_success_message(self, mock_print):
        self.mock_db.add_task.return_value = 4
        self.todo_list.add_task("Test task")
        mock_print.assert_called_once_with("Task 'Test task' added successfully!")

    def test_add_task_refresh_called(self):
        self.mock_db.add_task.return_value = 5
        self.todo_list.refresh_tasks = Mock()
        self.todo_list.add_task("Test task")
        self.todo_list.refresh_tasks.assert_called_once()
