from python.todo import TodoList
import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, call
import logging
from python.database import DatabaseError
from python.logging_config import setup_logging

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

    def test_refresh_tasks_with_deadline_dates(self):
        """Verify refresh_tasks correctly handles tasks with deadline dates."""
        # Prepare test data with various deadline dates
        test_date_1 = datetime(2023, 12, 31)
        test_date_2 = datetime(2024, 1, 1)
        test_tasks = [
            (1, "Task with date", test_date_1, None, None, None),
            (2, "Task with different date", test_date_2, "Work", None, 1),
            (3, "Task without date", None, None, None, None)
        ]

        # Configure mock
        self.mock_db.get_all_tasks.return_value = test_tasks

        # Call refresh_tasks
        self.todo_list.refresh_tasks()

        # Verify
        self.mock_db.get_all_tasks.assert_called_once()
        self.assertEqual(self.todo_list.tasks, test_tasks)
        self.assertEqual(self.todo_list.tasks[0][2], test_date_1)
        self.assertEqual(self.todo_list.tasks[1][2], test_date_2)
        self.assertIsNone(self.todo_list.tasks[2][2])

    def test_refresh_tasks_with_priority_levels(self):
        """Verify refresh_tasks correctly handles tasks with different priority levels."""
        test_tasks = [
            (1, "High priority", None, None, None, 1),
            (2, "Medium priority", None, None, None, 5),
            (3, "Low priority", None, None, None, 10),
            (4, "Zero priority", None, None, None, 0),
            (5, "Negative priority", None, None, None, -1)
        ]

        self.mock_db.get_all_tasks.return_value = test_tasks

        self.todo_list.refresh_tasks()

        self.assertEqual(self.todo_list.tasks, test_tasks)
        self.assertEqual(self.todo_list.tasks[0][5], 1)
        self.assertEqual(self.todo_list.tasks[4][5], -1)

    def test_refresh_tasks_with_special_characters(self):
        """Verify refresh_tasks correctly handles tasks with special characters."""
        test_tasks = [
            (1, "Task with @#$%^&*", None, "Category with !@#", "Notes with €£¥", 1),
            (2, "Empty spaces   ", None, "   Leading spaces", "Trailing spaces   ", 2),
            (3, "Unicode chars 你好", None, "Category 你好", "Notes 你好", 3),
            (4, "Escaped chars \n\t\r", None, None, None, 4)
        ]

        self.mock_db.get_all_tasks.return_value = test_tasks

        self.todo_list.refresh_tasks()

        self.assertEqual(self.todo_list.tasks, test_tasks)
        self.assertEqual(self.todo_list.tasks[0][1], "Task with @#$%^&*")
        self.assertEqual(self.todo_list.tasks[2][1], "Unicode chars 你好")

    def test_refresh_tasks_with_long_strings(self):
        """Verify refresh_tasks correctly handles tasks with very long strings."""
        long_task = "x" * 1000  # 1000 character string
        long_category = "y" * 500
        long_notes = "z" * 2000

        test_tasks = [
            (1, long_task, None, long_category, long_notes, 1)
        ]

        self.mock_db.get_all_tasks.return_value = test_tasks

        self.todo_list.refresh_tasks()

        self.assertEqual(self.todo_list.tasks, test_tasks)
        self.assertEqual(len(self.todo_list.tasks[0][1]), 1000)
        self.assertEqual(len(self.todo_list.tasks[0][3]), 500)
        self.assertEqual(len(self.todo_list.tasks[0][4]), 2000)
        
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

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.refresh_tasks()

            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Database error", str(context.exception))
            self.assertEqual(self.todo_list.tasks, [])
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to refresh tasks: %s" 
                and "Database error" in call.args[1]
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'refresh_tasks'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'refresh_tasks'
                for call in calls
            ))

            # Verify mock was called
            self.mock_db.get_all_tasks.assert_called_once()

    def test_refresh_tasks_connection_timeout(self):
        """Verify refresh_tasks handles connection timeouts correctly."""
        # Configure mock
        self.mock_db.get_all_tasks.side_effect = TimeoutError("Connection timeout")

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.refresh_tasks()

            # Verify error handling
            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Connection timeout", str(context.exception))
            self.assertEqual(self.todo_list.tasks, [])
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to refresh tasks: %s" 
                and "Connection timeout" in call.args[1]
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'refresh_tasks'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'refresh_tasks'
                for call in calls
            ))
            
            # Verify mock was called
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
        # Set up mock tasks as a list for len() to work
        self.todo_list.tasks = []

    def test_add_task_basic(self):
        """Verify basic task creation with minimal parameters."""
        self.mock_db.add_task.return_value = self.TASK_IDS['BASIC']
        # Mock get_all_tasks to return a list for refresh_tasks
        self.mock_db.get_all_tasks.return_value = [(1, "Test task", None, None, None, None)]
        
        task_id = self.todo_list.add_task(self.BASIC_TASK)
        
        self.mock_db.add_task.assert_called_once_with(self.BASIC_TASK, None, None, None, None)
        self.assertEqual(task_id, self.TASK_IDS['BASIC'])

    def test_add_task_with_all_parameters(self):
        """Verify task creation with all available parameters."""
        # Setup mocks
        self.mock_db.add_task.return_value = self.TASK_IDS['FULL']
        self.mock_db.get_all_tasks.return_value = [(1, "Test task", None, None, None, None)]
        
        deadline = datetime.now()
        task_data = self.FULL_TASK_DATA.copy()

        task_id = self.todo_list.add_task(
            task_data['title'],
            deadline=deadline,
            category=task_data['category'],
            notes=task_data['notes'],
            priority=task_data['priority']
        )

        # Verify add_task call
        self.mock_db.add_task.assert_called_once_with(
            task_data['title'],
            deadline,
            task_data['category'],
            task_data['notes'],
            task_data['priority']
        )
        # Verify get_all_tasks was called for refresh
        self.mock_db.get_all_tasks.assert_called_once()
        self.assertEqual(task_id, self.TASK_IDS['FULL'])

    def test_add_task_with_partial_parameters(self):
        """Verify task creation with partial parameters."""
        # Setup mocks
        self.mock_db.add_task.return_value = self.TASK_IDS['PARTIAL']
        self.mock_db.get_all_tasks.return_value = [(1, "Test task", None, None, None, None)]
        task_data = self.PARTIAL_TASK_DATA

        task_id = self.todo_list.add_task(
            task_data['title'],
            category=task_data['category'],
            priority=task_data['priority']
        )

        # Verify add_task call
        self.mock_db.add_task.assert_called_once_with(
            task_data['title'],
            None,
            task_data['category'],
            None,
            task_data['priority']
        )
        # Verify get_all_tasks was called for refresh
        self.mock_db.get_all_tasks.assert_called_once()
        self.assertEqual(task_id, self.TASK_IDS['PARTIAL'])

    def test_add_task_success_message(self):
        """Verify success message is logged after task creation."""
        # Ensure logging is configured
        setup_logging(__name__)
        
        # Setup mocks
        self.mock_db.add_task.return_value = self.TASK_IDS['SUCCESS_MSG']
        self.mock_db.get_all_tasks.return_value = [(1, "Test task", None, None, None, None)]

        with self.assertLogs('python.todo', level='INFO') as log:
            self.todo_list.add_task(self.BASIC_TASK)

            expected_calls = [
                "INFO:python.todo:Successfully refreshed 1 tasks",
                "INFO:python.todo:Successfully added task [TaskID: 4]"
            ]
            for expected_call in expected_calls:
                self.assertTrue(any(expected_call in message for message in log.output))

    def test_add_task_refresh_called(self):
        """Verify task list is refreshed after adding a task."""
        self.mock_db.add_task.return_value = self.TASK_IDS['REFRESH']
        self.todo_list.refresh_tasks = Mock()
        self.todo_list.add_task(self.BASIC_TASK)
        self.todo_list.refresh_tasks.assert_called_once()

    def test_add_task_database_error(self):
        """Verify database error handling during task addition."""
        self.mock_db.add_task.side_effect = DatabaseError("Database error", code=1)
        
        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.add_task(self.BASIC_TASK)

            self.assertIn("Database error", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to add task - Error: %s" 
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'add_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'add_task'
                for call in calls
            ))

    def test_add_task_timeout_error(self):
        """Verify timeout error handling during task addition."""
        self.mock_db.add_task.side_effect = TimeoutError("Connection timeout")
        
        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.add_task(self.BASIC_TASK)

            self.assertIn("Connection timeout", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to add task - Error: %s" 
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'add_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'add_task'
                for call in calls
            ))

    def test_add_task_invalid_input(self):
        """Verify invalid input handling."""
        invalid_inputs = [None, "", 123, [], {}]

        for invalid_input in invalid_inputs:
            with self.assertRaises(ValueError) as context:
                self.todo_list.add_task(invalid_input)
            self.assertIn("Task must be a non-empty string", str(context.exception))

class TestTodoListMarkCompleted(BaseTodoListTest):
    """Test suite for mark_completed method of TodoList class."""

    def setUp(self):
        super().setUp()

    def test_mark_completed_successful(self):
        """Verify successful task completion."""
        # Setup test data
        test_tasks = [
            (1, "Task 1", None, None, None, None, False),
            (2, "Task 2", None, None, None, None, False)
        ]
        self.todo_list.tasks = test_tasks

        # Mock get_task to return uncompleted task
        self.mock_db.get_task.return_value = test_tasks[0]

        # Mock successful completion
        self.mock_db.mark_completed.return_value = True
        self.todo_list.refresh_tasks = Mock()

        # Execute test
        self.todo_list.mark_completed(0)

        # Verify behavior
        self.mock_db.mark_completed.assert_called_once_with(1)
        self.todo_list.refresh_tasks.assert_called_once()
        self.mock_db.get_task.assert_called_once_with(1)

    def test_mark_completed_invalid_index(self):
        """Verify that mark_completed raises an IndexError for an invalid task index."""
        with self.assertRaises(IndexError) as context:
            self.todo_list.mark_completed(-1)
        self.assertIn("Invalid task index", str(context.exception))

    def test_mark_completed_timeout_error(self):
        """Verify timeout error handling during task completion."""
        # Setup test data - (id, title, deadline, category, notes, priority, completed)
        test_tasks = [
            (1, "Task 1", None, None, None, None, False),
            (2, "Task 2", None, None, None, None, False)
        ]
        self.todo_list.tasks = test_tasks

        # Mock get_task to return complete task data
        self.mock_db.get_task.return_value = test_tasks[0]

        # Configure mock for timeout
        self.mock_db.mark_completed.side_effect = TimeoutError("Connection timeout")

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.mark_completed(0)

            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Connection timeout", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to mark task as completed - Error: %s" 
                and call.args[1] == "Connection timeout"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'mark_completed'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'mark_completed'
                for call in calls
            ))
            
            # Verify mock calls
            self.mock_db.get_task.assert_called_once_with(1)
            self.mock_db.mark_completed.assert_called_once_with(1)

    def test_mark_completed_database_error(self):
        """Verify database error handling during task completion."""
        # Set up test data with complete task tuple structure
        test_tasks = [
            (1, "Task 1", None, None, None, None, False),
            (2, "Task 2", None, None, None, None, False)
        ]
        self.todo_list.tasks = test_tasks

        # Mock get_task to return valid task data
        self.mock_db.get_task.return_value = test_tasks[0]

        # Configure mock for database error
        self.mock_db.mark_completed.side_effect = DatabaseError("Database error", code=1)

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.mark_completed(0)

            self.assertIn("Database error", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to mark task as completed - Error: %s" 
                and call.args[1] == "Database error"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'mark_completed'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'mark_completed'
                for call in calls
            ))

            self.mock_db.get_task.assert_called_once_with(1)
            self.mock_db.mark_completed.assert_called_once_with(1)

    def test_mark_completed_already_completed(self):
        """Verify that mark_completed raises ValueError when task is already completed."""
        # Set up test data
        test_tasks = [(1, "Task 1"), (2, "Task 2")]
        self.todo_list.tasks = test_tasks

        # Mock get_task to return a completed task (completion status at index 6)
        self.mock_db.get_task.return_value = (1, "Task 1", None, None, None, None, True)

        # Verify ValueError is raised
        with patch('python.todo.log.warning') as mock_log_warning:
            with self.assertRaises(ValueError) as context:
                self.todo_list.mark_completed(0)

            self.assertIn("Task is already marked as completed", str(context.exception))
            mock_log_warning.assert_called_once_with("Task is already marked as completed")

        # Verify mark_completed was not called since task was already completed
        self.mock_db.mark_completed.assert_not_called()

class TestTodoListUpdateTask(BaseTodoListTest):
    """Test suite for update_task method of TodoList class."""
    
    def setUp(self):
        super().setUp()

    def test_update_task_successful(self):
        """Verify successful task update."""
        test_tasks = [(1, "Task 1"), (2, "Task 2")]
        self.todo_list.tasks = test_tasks
        self.todo_list.refresh_tasks = Mock()
        updates = {"task": "Updated Task", "priority": 1}

        self.todo_list.update_task(0, **updates)

        self.mock_db.update_task.assert_called_once_with(1, **updates)
        self.todo_list.refresh_tasks.assert_called_once()

    def test_update_task_invalid_index(self):
        """Verify that update_task raises IndexError for invalid index."""
        with self.assertRaises(IndexError) as context:
            self.todo_list.update_task(-1, task="Updated")
        self.assertIn("Invalid task index", str(context.exception))

    def test_update_task_database_error(self):
        """Verify database error handling during task update."""
        test_tasks = [(1, "Task 1")]
        self.todo_list.tasks = test_tasks
        self.mock_db.update_task.side_effect = DatabaseError("Database error", code=1)

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.update_task(0, task="Updated")
                
            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Database error", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to update task - Error: %s" 
                and call.args[1] == "Database error"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'update_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'update_task'
                for call in calls
            ))

            # Verify mock was called with correct arguments
            self.mock_db.update_task.assert_called_once_with(1, task="Updated")

    def test_update_task_timeout_error(self):
        """Verify timeout error handling during task update."""
        test_tasks = [(1, "Task 1")]
        self.todo_list.tasks = test_tasks
        self.mock_db.update_task.side_effect = TimeoutError("Connection timeout")

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.update_task(0, task="Updated")

            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Connection timeout", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to update task - Error: %s" 
                and call.args[1] == "Connection timeout"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'update_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'update_task'
                for call in calls
            ))

            # Verify mock was called with correct arguments
            self.mock_db.update_task.assert_called_once_with(1, task="Updated")

    def test_update_task_multiple_fields(self):
        """Verify updating multiple task fields at once."""
        test_tasks = [(1, "Task 1")]
        self.todo_list.tasks = test_tasks
        self.todo_list.refresh_tasks = Mock()
        updates = {
            "task": "Updated Task",
            "deadline": datetime.now(),
            "category": "Work",
            "notes": "Important",
            "priority": 1
        }

        self.todo_list.update_task(0, **updates)
        
        self.mock_db.update_task.assert_called_once_with(1, **updates)
        self.todo_list.refresh_tasks.assert_called_once()

class TestTodoListDeleteTask(BaseTodoListTest):
    """Test suite for delete_task method of TodoList class."""

    def setUp(self):
        super().setUp()

    def test_delete_task_successful(self):
        """Verify successful task deletion."""
        # Setup test data
        test_tasks = [
            (1, "Task 1", None, None, None, None)
        ]
        self.todo_list.tasks = test_tasks
        self.todo_list.refresh_tasks = Mock()

        # Execute test
        self.todo_list.delete_task(0)

        # Verify behavior
        self.mock_db.delete_task.assert_called_once_with(1)
        self.todo_list.refresh_tasks.assert_called_once()

    def test_delete_task_invalid_index(self):
        """Verify that delete_task raises IndexError for invalid index."""
        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(IndexError) as context:
                self.todo_list.delete_task(-1)
                
            self.assertIn("Invalid task index", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Invalid task index [TaskIndex: %d]"
                and call.args[1] == -1
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'delete_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'delete_task'
                for call in calls
            ))

    def test_delete_task_database_error(self):
        """Verify database error handling during task deletion."""
        # Setup test data
        test_tasks = [(1, "Task 1")]
        self.todo_list.tasks = test_tasks
        
        # Configure mocks in correct order
        self.mock_db.get_task.return_value = (1, "Task 1", None, None, None, None)
        self.mock_db.delete_task.side_effect = DatabaseError("Database error", code=1)

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.delete_task(0)
                
            self.assertIn("Database operation failed", str(context.exception))
            self.assertIn("Database error", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to delete task - Error: %s" 
                and call.args[1] == "Database error"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'delete_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'delete_task'
                for call in calls
            ))
            
            # Order of verification is important
            self.mock_db.get_task.assert_called_once_with(1)
            self.mock_db.delete_task.assert_called_once_with(1)

    def test_delete_task_timeout_error(self):
        """Verify timeout error handling during task deletion."""
        # Setup test data 
        test_tasks = [(1, "Task 1")]
        self.todo_list.tasks = test_tasks
        
        # Configure mocks in correct order
        self.mock_db.get_task.return_value = (1, "Task 1", None, None, None, None)
        self.mock_db.delete_task.side_effect = TimeoutError("Connection timeout")

        with patch('python.todo.log.error') as mock_log_error:
            with self.assertRaises(RuntimeError) as context:
                self.todo_list.delete_task(0)
                
            self.assertIn("Connection timeout", str(context.exception))
            
            # Verify that error was logged multiple times due to decorators
            calls = mock_log_error.call_args_list
            self.assertEqual(len(calls), 4)  # Expect 4 error log calls
            
            # Verify the specific error messages
            self.assertTrue(any(
                call.args[0] == "Failed to delete task - Error: %s" 
                and call.args[1] == "Connection timeout"
                and call.kwargs.get('exc_info') == True
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == 'Failed %s [OperationID: %s] - Error: %s'
                and call.args[1] == 'delete_task'
                for call in calls
            ))
            self.assertTrue(any(
                call.args[0] == "Function '%s' failed after %.2f seconds - Error: %s"
                and call.args[1] == 'delete_task'
                for call in calls
            ))
            
            # Order of verification is important
            self.mock_db.get_task.assert_called_once_with(1)
            self.mock_db.delete_task.assert_called_once_with(1)

class TestTodoListLogging(BaseTodoListTest):
    """Test suite for TodoList logging functionality."""

    def setUp(self):
        """Set up test environment with proper mocks."""
        super().setUp()
        self.logger = setup_logging("test_todo")
        # Setup mock database to return a list for get_all_tasks
        self.mock_db.get_all_tasks.return_value = [(1, "Test Task", None, None, None, None)]
        # Initialize tasks list as a real list
        self.todo_list.tasks = []
        # Setup mock for add_task to return a task ID
        self.mock_db.add_task.return_value = 1

    def test_operation_logging(self):
        """Test operation logging in TodoList methods"""
        with self.assertLogs('python.todo', level='INFO') as log:
            self.todo_list.add_task("Test Task")
            
            log_output = log.output
            self.assertTrue(any("[OperationID:" in msg for msg in log_output))
            self.assertTrue(any("add_task" in msg for msg in log_output))

    def test_error_logging(self):
        """Test error logging with operation context"""
        with self.assertLogs('python.todo', level='ERROR') as log:
            try:
                self.todo_list.add_task("")
            except ValueError:
                pass

            log_output = log.output
            self.assertTrue(any("Invalid task parameter" in msg for msg in log_output))
            self.assertTrue(any("[OperationID:" in msg for msg in log_output))

    def test_performance_logging(self):
        """Test execution time logging"""
        with self.assertLogs('python.todo', level='DEBUG') as log:
            self.todo_list.refresh_tasks()
            
            log_output = log.output
            self.assertTrue(any("executed in" in msg for msg in log_output))
