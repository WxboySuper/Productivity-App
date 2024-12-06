import unittest
from unittest.mock import patch
import sqlite3
from datetime import datetime
from src.python.database import TodoDatabase, DatabaseError
import os
import time

#skipcq: PTC-W0046
class BaseTodoDatabaseTest(unittest.TestCase):
    """Base test class for TodoDatabase class."""
    
    # Test data constants
    BASIC_TASK_TITLE = "Test Task"
    
    # Full task data
    FULL_TASK_DATA = {
        'title': "Complete Project",
        'completed': False,
        'category': "Work",
        'notes': "Important project deadline",
        'priority': "1"
    }
    
    # Partial task data
    PARTIAL_TASK_DATA = {
        'title': "Partial Task",
        'category': "Personal",
        'priority': "2"
    }

    # Database field mapping
    FIELD_MAPPING = {
        1: 'title',
        2: 'deadline', 
        3: 'category',
        4: 'notes',
        5: 'priority'
    }


    # Invalid data
    INVALID_PRIORITY = '-1'

    # Test database configuration
    TEST_DB_DIR = os.path.join(os.path.dirname(__file__), 'test_databases')
    TEST_DB_NAME = os.path.join(TEST_DB_DIR, 'test_todo.db')

    def wait_for_file_operation(self, condition_func, timeout=5, initial_delay=0.1):
        """Wait for file operation with exponential backoff."""
        delay = initial_delay
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            if condition_func():
                return True
            time.sleep(delay)
            delay = min(delay * 2, timeout)
        
        return False

    @classmethod
    def setUpClass(cls):
        """Create test database directory."""
        os.makedirs(cls.TEST_DB_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Remove all test databases."""
        if os.path.exists(cls.TEST_DB_DIR):
            time.sleep(1.0)  # Increased delay
            for file in os.listdir(cls.TEST_DB_DIR):
                max_retries = 3
                for _ in range(max_retries):
                    try:
                        file_path = os.path.join(cls.TEST_DB_DIR, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.5)
            try:
                os.rmdir(cls.TEST_DB_DIR)
            except PermissionError:
                pass
            except OSError:
                pass

    def setUp(self):
        """Initialize test database before each test case."""
        self.wait_for_file_operation(
            lambda: not os.path.exists(self.TEST_DB_NAME)
        )
        
        # Retry mechanism for file operations
        max_retries = 3
        for _ in range(max_retries):
            try:
                if os.path.exists(self.TEST_DB_NAME):
                    os.remove(self.TEST_DB_NAME)
                break
            except PermissionError:
                time.sleep(0.5)
        
        # Create new database instance
        self.db = TodoDatabase(self.TEST_DB_NAME)

    def tearDown(self):
        """Clean up test database after each test case."""
        if hasattr(self, 'db'):
            del self.db
        
        self.wait_for_file_operation(
            lambda: not os.path.exists(self.TEST_DB_NAME)
        )
        
        max_retries = 3
        for _ in range(max_retries):
            try:
                if os.path.exists(self.TEST_DB_NAME):
                    os.remove(self.TEST_DB_NAME)
                break
            except PermissionError:
                time.sleep(0.5)

class TestTodoDatabaseAddTask(BaseTodoDatabaseTest):
    """Test suite for add_task function in TodoDatabase class."""
    
    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_add.db')

    def setUp(self):
        super().setUp()

    def test_add_task_basic(self):
        """Verify basic task creation with minimal required fields."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        self.assertIsInstance(task_id, int)
        self.assertTrue(task_id > 0)

    def test_add_task_with_all_fields(self):
        """Verify task creation with all available fields populated."""
        deadline_var = datetime.now()
        deadline_str = deadline_var.strftime('%Y-%m-%d %H:%M:%S')
        
        task_data = self.FULL_TASK_DATA.copy()
        task_data['deadline'] = deadline_str

        task_id = self.db.add_task(
            title=task_data['title'],
            deadline=task_data['deadline'],
            category=task_data['category'],
            notes=task_data['notes'],
            priority=task_data['priority']
        )

        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, deadline, category, notes, priority FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
        
        # Explicitly specify the column indices based on the SELECT statement order
        self.assertEqual(task[0], task_id)  # id
        self.assertEqual(task[1], task_data['title'])  # title
        self.assertEqual(task[2], task_data['deadline'])  # deadline
        self.assertEqual(task[3], task_data['category'])  # category
        self.assertEqual(task[4], task_data['notes'])  # notes
        self.assertEqual(task[5], int(task_data['priority']))  # priority

    def test_add_task_with_partial_fields(self):
        """Verify task creation with only some fields populated."""
        task_id = self.db.add_task(
            title=self.PARTIAL_TASK_DATA['title'],
            category=self.PARTIAL_TASK_DATA['category'],
            priority=self.PARTIAL_TASK_DATA['priority']
        )
        
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, deadline, category, notes, priority FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
            
        self.assertEqual(task[1], self.PARTIAL_TASK_DATA['title'])
        self.assertIsNone(task[2] or None)  # Convert SQLite NULL (0) to Python None
        self.assertEqual(task[3], self.PARTIAL_TASK_DATA['category'])
        self.assertIsNone(task[4] or None)  # Convert SQLite NULL (0) to Python None

    def test_add_task_empty_title(self):
        """Verify that empty task titles are rejected."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_task("")
        self.assertEqual(cm.exception.code, "EMPTY_TITLE")

    def test_add_task_none_title(self):
        """Verify that None task titles are rejected."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_task(None)
        self.assertEqual(cm.exception.code, "INVALID_TITLE")

    def test_add_task_invalid_priority(self):
        """Verify that invalid priority values are rejected."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_task(self.BASIC_TASK_TITLE, priority=self.INVALID_PRIORITY)
        self.assertEqual(cm.exception.code, "INVALID_PRIORITY")

class TestTodoDatabaseDeleteTask(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase class delete_task method."""
    
    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_delete.db')

    def setUp(self):
        super().setUp()

    # Test Suite for delete_task Functionality
    def test_task_delete(self):
        """Verify that a task can be deleted by its ID."""
        deadline_var = datetime.now()
        deadline_str = deadline_var.strftime('%Y-%m-%d %H:%M:%S')
        
        task_data = self.FULL_TASK_DATA.copy()
        task_data['deadline'] = deadline_str

        task_id = self.db.add_task(
            title=task_data['title'],
            deadline=task_data['deadline'],
            category=task_data['category'],
            notes=task_data['notes'],
            priority=task_data['priority']
        )

        task = self.db.get_task(task_id)
        self.assertIsNotNone(task)

        self.db.delete_task(task_id)

        with self.assertRaises(DatabaseError) as cm:
            self.db.get_task(task_id)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")

    def test_delete_nonexistent_task(self):
        """Verify that attempting to delete a non-existent task raises an error."""
        with self.assertRaises(DatabaseError):
            self.db.delete_task(9999)
    
    @patch('sqlite3.connect')
    def test_delete_task_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect to the database")
        with self.assertRaises(DatabaseError) as cm:
            self.db.delete_task(1)
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseUpdateTask(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase class update_task method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_update.db')

    def setUp(self):
        super().setUp()
    
    def test_update_task_successful(self):
        """Verify that a task can be successfully updated with valid fields."""
        task_data = self.FULL_TASK_DATA
        deadline_var = datetime.now()
        deadline_str = deadline_var.strftime('%Y-%m-%d %H:%M:%S')
        task_id = self.db.add_task(
            title=task_data['title'],
            deadline=deadline_str,
            category=task_data['category'],
            notes=task_data['notes'],
            priority=task_data['priority']
        )
        
        updates = {
                'title': "Updated Task Title",
                'completed': True,
                'deadline': deadline_str,
                'category': "Updated Category",
                'notes': "Updated Notes",
                'priority': "2"
            }

        self.db.update_task(task_id, **updates)

        task = self.db.get_task(task_id)
        # Verify each field with type-specific assertions
        self.assertIsInstance(task[1], str, "Title should be a string")
        self.assertEqual(task[1], updates['title'])
        self.assertIsInstance(task[2], bool, "Completed should be a boolean")
        self.assertTrue(task[2])
        self.assertIsInstance(task[3], str, "Deadline should be a string")
        self.assertEqual(task[3], updates['deadline'])
        self.assertIsInstance(task[4], str, "Category should be a string")
        self.assertEqual(task[4], updates['category'])
        self.assertIsInstance(task[5], str, "Notes should be a string")
        self.assertEqual(task[5], updates['notes'])
        self.assertIsInstance(task[6], int, "Priority should be an integer")
        self.assertEqual(task[6], int(updates['priority']))
    
    def test_update_nonexistent_task(self):
        """Verify that updating a nonexistent task raises a DatabaseError."""
        updates = {'title': 'Nonexistent Task'}
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(9999, **updates)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")
    
    def test_update_task_with_invalid_field(self):
        """Verify that updating a task with an invalid field does not change the task."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {'invalid_field': "Invalid Value"}
        
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(task_id, **updates)
        self.assertEqual(cm.exception.code, "NO_UPDATES")

    def test_update_task_invalid_priority(self):
        """Verify that updating a task with an invalid priority raises a DatabaseError."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {'priority': self.INVALID_PRIORITY}
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(task_id, **updates)
        self.assertEqual(cm.exception.code, "INVALID_PRIORITY")
    
    def test_update_task_empty_title(self):
        """Verify that updating a task with an empty title raises a DatabaseError."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {'title': ""}
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(task_id, **updates)
        self.assertEqual(cm.exception.code, "EMPTY_TITLE")
    
    def test_update_task_none_title(self):
        """Verify that updating a task with a None title raises a DatabaseError."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {'title': None}
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(task_id, **updates)
        self.assertEqual(cm.exception.code, "INVALID_VALUE")

    def test_empty_update(self):
        """Verify that updating a task with an empty dictionary does not change the task."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {}
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(task_id, **updates)
        self.assertEqual(cm.exception.code, "NO_UPDATES")
        
    def test_update_task_empty_optional_fields(self):
        """Verify that empty strings are handled correctly for optional fields."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        updates = {'notes': "", 'category': ""}
        self.db.update_task(task_id, **updates)
        task = self.db.get_task(task_id)
        self.assertEqual(task[4], "")
        self.assertEqual(task[5], "")

    @patch('sqlite3.connect')
    def test_update_task_db_connection_error(self, mock_connect):
        """Verify that a database connection error during update is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect to the database")
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(1, title="New Title")
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseMarkCompleted(BaseTodoDatabaseTest):
    """"Test suite for TodoDatabase.get_task method."""
    
    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_mark_completed.db')

    def setUp(self):
        super().setUp()
    
    # Test Suite for mark_completed Functionality
    def test_mark_completed_successful(self):
        """Verify that a task can be successfully marked as completed."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        self.db.mark_completed(task_id)
        task = self.db.get_task(task_id)
        self.assertTrue(task[2])
    
    def test_mark_completed_nonexistent_task(self):
        """Verify that marking a nonexistent task as completed raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.mark_completed(9999)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")
    
    @patch('sqlite3.connect')
    def test_mark_completed_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
        with self.assertRaises(DatabaseError) as cm:
            self.db.mark_completed(1)
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseGetTask(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase.get_task method."""
    
    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_get.db')

    def setUp(self):
        super().setUp()

    # Test Suite for get_task Functionality
    def test_get_task_successful(self):
        """Verify that a task can be successfully retrieved."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        task = self.db.get_task(task_id)
        self.assertEqual(task[0], task_id,)
        self.assertEqual(task[1], self.BASIC_TASK_TITLE)
    
    def test_get_task_nonexistent_task(self):
        """Verify that retrieving a nonexistent task raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_task(9999)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")
    
    @patch('sqlite3.connect')
    def test_get_task_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_task(1)
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")
    
class TestTodoDatabaseGetAllTasks(BaseTodoDatabaseTest):
    """Separate test class for get_all_tasks functionality to ensure isolation."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_todo_get_all.db')

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if os.path.exists(cls.TEST_DB_NAME):
            try:
                os.remove(cls.TEST_DB_NAME)
            except PermissionError:
                time.sleep(1.0)  # Increased delay for Windows
                try:
                    os.remove(cls.TEST_DB_NAME)
                except PermissionError:
                    pass

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if os.path.exists(cls.TEST_DB_NAME):
            try:
                os.remove(cls.TEST_DB_NAME)
            except PermissionError:
                time.sleep(0.5)  # Wait longer if file is locked
                try:
                    os.remove(cls.TEST_DB_NAME)
                except PermissionError:
                    pass

    def setUp(self):
        super().setUp()

    def test_get_all_tasks_successful(self):
        """Verify that all tasks can be successfully retrieved."""
        self.db.add_task(self.BASIC_TASK_TITLE)
        self.db.add_task(self.BASIC_TASK_TITLE)
        
        tasks = self.db.get_all_tasks()
        self.assertEqual(len(tasks), 2)

    @patch('sqlite3.connect')
    def test_get_all_tasks_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        # Set up mock before creating database instance
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
        
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_all_tasks()
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

