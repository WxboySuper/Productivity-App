from src.python.todo import TodoList
import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, call
import logging
from src.python.database import DatabaseError

#skipcq: PTC-W0046
class BaseTodoListTest(unittest.TestCase):
    """Base test class for TodoList test suite."""

    # Test data
    BASIC_TASK = "Test task"

    TASK_IDS = {
        'BASIC': 1,
        'FULL': 2,
        'PARTIAL': 3,
        'SUCCESS_MSG': 4,
        'REFRESH': 5
    }

    PARTIAL_TASK_DATA = {
        'title': "Buy groceries",
        'category': "Personal",
        'priority': 2
    }

    FULL_TASK_DATA = {
        'title': "Complete project",
        'category': "Work",
        'notes': "Important project",
        'priority': 1
    }

    SUCCESS_MESSAGE = "Task 'Test task' added successfully!"

    TEST_DB_DIR = os.path.join(os.path.dirname(__file__), 'todo_test_databases')

    TEST_LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')

    LOG_PATH = os.path.join(TEST_LOG_DIR, 'todo_test.log')

    @classmethod
    def setUpClass(cls):
        """Create todo test directory."""
        os.makedirs(cls.TEST_DB_DIR, exist_ok=True)

    def setUp(self):
        """Set up test environment."""

        self.mock_db = Mock()
        self.todo_list = TodoList(db=self.mock_db)

        # Clear logs
        log_path = self.LOG_PATH
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            open(log_path, 'w').close()
        except IOError as e:
            print(f"Error clearing log file: {str(e)}")

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.TEST_DB_DIR):
            for file in os.listdir(self.TEST_DB_DIR):
                try:
                    os.remove(os.path.join(self.TEST_DB_DIR, file))
                except OSError as e:
                    self.fail(f"Failed to remove test file {file}: {str(e)}")
            try:
                os.rmdir(self.TEST_DB_DIR)
            except OSError as e:
                self.fail(f"Failed to remove test directory: {str(e)}")

class TestTodoListRefreshTasks(BaseTodoListTest):
    """Test suite for refresh_tasks method of TodoList class."""

    TEST_DB_NAME = os.path.join(BaseTodoListTest.TEST_DB_DIR, 'test_todo_refresh.db')

    def setUp(self):
        super().setUp()

    def test_refresh_tasks_successful(self):
        """Verify that refresh_tasks successfully updates the tasks list with database data."""
        # Prepare test data
        test_tasks = [
            (1, "Task 1", None, None, None, None),
            (2, "Task 2", None, "Work", None, 1),
            (3, "Task 3", None, "Personal", "Important", 2)
        ]

        # Configure mock to return test data
        self.mock_db.get_all_tasks.return_value = test_tasks

        # Call refresh_tasks
        self.todo_list.refresh_tasks()

        # Verify get_all_tasks was called
        self.mock_db.get_all_tasks.assert_called_once()

        # Verify tasks list was updated correctly
        self.assertEqual(self.todo_list.tasks, test_tasks)

    def test_refresh_tasks_empty(self):
        """Verify that refresh_tasks updates the tasks list with an empty list if no tasks are found in the database."""
        # Configure mock to return an empty list
        self.mock_db.get_all_tasks.return_value = []

        # Call refresh_tasks
        self.todo_list.refresh_tasks()

        # Verify get_all_tasks was called
        self.mock_db.get_all_tasks.assert_called_once()

        # Verify tasks list was updated correctly
        self.assertEqual(self.todo_list.tasks, [])

    def test_refresh_tasks_error(self):
        """Verify that refresh_tasks handles database errors correctly."""
        # Configure mock with correct DatabaseError constructor
        self.mock_db.get_all_tasks.side_effect = DatabaseError("Database error", code=1)

        with patch('logging.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.refresh_tasks()

            self.assertIn("Database error", str(context.exception))
            self.assertEqual(self.todo_list.tasks, [])
            mock_log_error.assert_called_once()
            self.mock_db.get_all_tasks.assert_called_once()

    def test_refresh_tasks_connection_timeout(self):
        """Verify refresh_tasks handles connection timeouts correctly."""
        # Configure mock
        self.mock_db.get_all_tasks.side_effect = TimeoutError("Connection timeout")

        with patch('logging.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.refresh_tasks()

            # Verify error handling - moved outside the assertRaises but inside the patch
            self.assertIn("Connection timeout", str(context.exception))
            self.assertEqual(self.todo_list.tasks, [])
            mock_log_error.assert_called_once()
            self.mock_db.get_all_tasks.assert_called_once()

    def test_refresh_tasks_state_change(self):
        """Verify tasks list state changes correctly during refresh."""
        initial_tasks = [(1, "Task 1")]
        new_tasks = [(2, "Task 2")]

        # Set initial state
        self.todo_list.tasks = initial_tasks
        self.mock_db.get_all_tasks.return_value = new_tasks

        self.todo_list.refresh_tasks()
        self.assertEqual(self.todo_list.tasks, new_tasks)

    def test_refresh_tasks_multiple_calls(self):
        """Verify multiple refresh calls work correctly."""
        self.mock_db.get_all_tasks.side_effect = [
            [(1, "Task 1")],
            [(1, "Task 1"), (2, "Task 2")],
            []
        ]

        # First refresh
        self.todo_list.refresh_tasks()
        self.assertEqual(len(self.todo_list.tasks), 1)

        # Second refresh
        self.todo_list.refresh_tasks()
        self.assertEqual(len(self.todo_list.tasks), 2)

        # Third refresh
        self.todo_list.refresh_tasks()
        self.assertEqual(len(self.todo_list.tasks), 0)

class TestTodoListAddTask(BaseTodoListTest):
    """Test suite for add_task method of TodoList class."""

    TEST_DB_NAME = os.path.join(BaseTodoListTest.TEST_DB_DIR, 'test_todo_add.db')

    def setUp(self):
        super().setUp()

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

    def test_add_task_success_message(self):
        """Verify success message is logged after task creation."""
        # Reset logging configuration
        logging.getLogger().handlers = []

        with patch('logging.info') as log_info:
            self.todo_list.add_task(self.BASIC_TASK)

            expected_calls = [
                call('Tasks refreshed successfully'),
                call("Task '%s' added successfully!", self.BASIC_TASK)
            ]
            log_info.assert_has_calls(expected_calls, any_order=False)

    def test_add_task_refresh_called(self):
        """Verify task list is refreshed after adding a task."""
        self.mock_db.add_task.return_value = self.TASK_IDS['REFRESH']
        self.todo_list.refresh_tasks = Mock()
        self.todo_list.add_task(self.BASIC_TASK)
        self.todo_list.refresh_tasks.assert_called_once()
    
    def test_add_task_database_error(self):
        """Verify database error handling during task addition."""
        self.mock_db.add_task.side_effect = DatabaseError("Database error", code=1)
        
        with patch('logging.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.add_task(self.BASIC_TASK)
            
            self.assertIn("Database error", str(context.exception))
            mock_log_error.assert_called_once()

    def test_add_task_timeout_error(self):
        """Verify timeout error handling during task addition."""
        self.mock_db.add_task.side_effect = TimeoutError("Connection timeout")

        with patch('logging.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.add_task(self.BASIC_TASK)

            self.assertIn("Connection timeout", str(context.exception))
            mock_log_error.assert_called_once()

    def test_add_task_invalid_input(self):
        """Verify invalid input handling."""
        invalid_inputs = [None, "", 123, [], {}]
        
        for invalid_input in invalid_inputs:
            with self.assertRaises(ValueError) as context:
                self.todo_list.add_task(invalid_input)
            self.assertIn("Task must be a non-empty string", str(context.exception))
