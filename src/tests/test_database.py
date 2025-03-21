import unittest
from unittest.mock import patch, Mock, call
import sqlite3
from datetime import datetime
from python.database import TodoDatabase, DatabaseError
import os
import time
import warnings
from contextlib import suppress
import sys
import shutil

#skipcq: PTC-W0046
class BaseTodoDatabaseTest(unittest.TestCase):
    """Base test class for TodoDatabase class."""

    # Test data constants
    BASIC_TASK_TITLE = "Test Task"

    BASIC_LABEL_TITLE = "Test Label"

    # Full task data
    FULL_TASK_DATA = {
        'title': "Complete Project",
        'completed': False,
        'category': "Work",
        'notes': "Important project deadline",
        'priority': "HIGH"
    }

    # Partial task data
    PARTIAL_TASK_DATA = {
        'title': "Partial Task",
        'category': "Personal",
        'priority': "MEDIUM"
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

    TEST_DB_DIR = os.path.join(os.path.dirname(__file__), 'test_databases')
    _connection_pool = {}

    @classmethod
    def setUpClass(cls):
        """Create test database directory."""
        os.makedirs(cls.TEST_DB_DIR, exist_ok=True)

    def setUp(self):
        """
        Set up test environment.
        Initializes the test environment and sets up warning capture
        to record and track all warnings during test execution.
        """
        self.recorded_warnings = []
        self.warning_context = warnings.catch_warnings(record=True)
        self.warning_context.__enter__()
        warnings.simplefilter("always")
        warnings.showwarning = self._record_warning
        self._remove_db_file()
        self.db = TodoDatabase(self.TEST_DB_NAME)

    def _record_warning(self, message, category, filename, lineno, *args, **kwards):
        """
        Record a warning message.
        Args:
            message: The warning message
            category: The warning category (e.g., DeprecationWarning)
            filename: The file where the warning occured
            lineno: The line number where the warning occured
            *args: Additional positional arguments from the warning
            **kwards: Additional keyword arguments from the warning
        """
        self.recorded_warnings.append(warnings.WarningMessage(
            message=str(message),
            category=category,
            filename=filename,
            lineno=lineno,
            line=None,
            file=None,
            source=None
        ))

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'db'):
            del self.db

    @classmethod
    def tearDownClass(cls):
        """Clean up test files after all tests."""
        with suppress(Exception):
            if os.path.exists(cls.TEST_DB_NAME):
                os.remove(cls.TEST_DB_NAME)
            if os.path.exists(cls.TEST_DB_DIR):
                os.rmdir(cls.TEST_DB_DIR)

    def _remove_db_file(self):
        """Helper to safely remove database file."""
        if not hasattr(self, 'TEST_DB_NAME') or ':memory:' in self.TEST_DB_NAME:
            return

        max_retries = 5
        for i in range(max_retries):
            try:
                if os.path.exists(self.TEST_DB_NAME):
                    os.remove(self.TEST_DB_NAME)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.1)
                continue

    @classmethod
    def get_connection(cls, db_name):
        """Get database connection from pool."""
        if db_name not in cls._connection_pool:
            conn = sqlite3.connect(db_name)
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            cls._connection_pool[db_name] = conn
        return cls._connection_pool[db_name]

class TestTodoDatabaseAddTask(BaseTodoDatabaseTest):
    """Test suite for add_task function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_add.db')

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
        self.assertEqual(task[5], task_data['priority'])  # priority

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

    def test_add_task_db_conn_error(self):
        """Verify that a database connection error is handled correctly."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.add_task(self.BASIC_TASK_TITLE)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

    def test_add_task_db_query_error(self):
        """Verify that a database query error is handled correctly."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cursor = mock_conn.cursor.return_value
            # Mock the execute method to raise a SQLite error
            mock_cursor.execute.side_effect = sqlite3.Error("Query error")
            # Mock the __enter__ and __exit__ methods for context manager
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.__exit__.side_effect = None
            
            with self.assertRaises(DatabaseError) as cm:
                self.db.add_task(self.BASIC_TASK_TITLE)
            self.assertEqual(cm.exception.code, "DB_QUERY_ERROR")

class TestTodoDatabaseDeleteTask(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase class delete_task method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_delete.db')

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
        with self.assertRaises(DatabaseError) as cm:
            self.db.delete_task(9999)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")

    @patch('sqlite3.connect')
    def test_delete_task_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect to the database")
        with self.assertRaises(DatabaseError) as cm:
            self.db.delete_task(1)
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseUpdateTask(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase class update_task method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_update.db')

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
                'priority': "MEDIUM"
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
        self.assertIsInstance(task[6], str, "Priority should be a string")
        self.assertEqual(task[6], updates['priority'])

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

    @patch('sqlite3.connect')
    def test_update_task_db_query_error(self, mock_connect):
        """Verify that database query error is handled correctly."""
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.execute.side_effect = sqlite3.Error("Query error")
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.side_effect = None

        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(1, title="New Title")
        self.assertEqual(cm.exception.code, "DB_QUERY_ERROR")

class TestTodoDatabaseMarkCompleted(BaseTodoDatabaseTest):
    """"Test suite for TodoDatabase.get_task method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_mark_completed.db')

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

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_get.db')

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

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_get_all.db')

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

class TestTodoDatabaseAddLabel(BaseTodoDatabaseTest):
    """Test suite for add_label function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_add_label.db')

    def setUp(self):
        super().setUp()
    
    def test_add_label_successful(self):
        """Verify that a label can be successfully added."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        self.assertIsNotNone(label_id)
        label = self.db.get_label(label_id)
        self.assertEqual(label[0], label_id)

    def test_add_label_with_color(self):
        """Verify that a label can be added with a color value."""
        test_name = f"ColorLabel_{int(time.time())}"  # Unique name
        test_color = "#FF0000"

        # Verify schema first
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(labels)")
            columns = [col[1] for col in cursor.fetchall()]
            self.assertIn('color', columns, "Labels table missing color column")

        # Add label with color
        label_id = self.db.add_label(test_name, color=test_color)
        self.assertIsNotNone(label_id, "Should return valid label ID")

        # Verify using explicit column names
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, color 
                FROM labels 
                WHERE id = ?
            """, (label_id,))
            label = cursor.fetchone()

            self.assertIsNotNone(label, f"Label {label_id} not found")
            self.assertEqual(label[0], label_id, "ID mismatch")
            self.assertEqual(label[1], test_name, "Name mismatch")
            self.assertEqual(
                label[2], 
                test_color, 
                f"Color mismatch: expected '{test_color}', got '{label[2]}'"
            )

    def test_add_duplicate_label(self):
        """Verify that adding a duplicate label returns the existing label's ID."""
        first_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        second_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        self.assertEqual(first_id, second_id)

    def test_add_label_empty_name(self):
        """Verify that adding a label with empty name raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_label("")
        self.assertEqual(cm.exception.code, "EMPTY_LABEL")

    def test_add_label_none_name(self):
        """Verify that adding a label with None name raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_label(None)
        self.assertEqual(cm.exception.code, "INVALID_LABEL")

    def test_add_label_whitespace_name(self):
        """Verify that adding a label with whitespace name raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_label("   ")
        self.assertEqual(cm.exception.code, "EMPTY_LABEL")

    @patch('sqlite3.connect')
    def test_add_label_db_connection_error(self, mock_connect):
        """Verify that a database connection error is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
        with self.assertRaises(DatabaseError) as cm:
            self.db.add_label(self.BASIC_LABEL_TITLE)
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

    def test_add_label_persists(self):
        """Verify that added labels persist in the database."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)

        # Create new database instance to verify persistence
        new_db = TodoDatabase(self.TEST_DB_NAME)
        labels = new_db.get_all_labels()
        self.assertTrue(any(label[0] == label_id for label in labels))
    
    @patch('sqlite3.connect')
    def test_add_label_db_query_error(self, mock_connect):
        """Verify that database query error is handled correctly."""
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.execute.side_effect = sqlite3.Error("Query error")
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.side_effect = None

        with self.assertRaises(DatabaseError) as cm:
            self.db.add_label(name="New Title")
        self.assertEqual(cm.exception.code, "DB_QUERY_ERROR")

class TestTodoDatabaseGetLabel(BaseTodoDatabaseTest):
    """Test suite for get_label function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_get_label.db')

    def setUp(self):
        super().setUp()

    def test_get_label_successful(self):
        """Verify that a label can be successfully retrieved by its ID."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        label = self.db.get_label(label_id)
        self.assertEqual(label[0], label_id)
        self.assertEqual(label[1], self.BASIC_LABEL_TITLE)

    def test_get_label_nonexistent_label(self):
        """Verify that attempting to retrieve a non-existent label raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_label(9999)
        self.assertEqual(cm.exception.code, "LABEL_NOT_FOUND")

    def test_get_label_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.get_label(label_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseDeleteLabel(BaseTodoDatabaseTest):
    """Test suite for delete_label function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_delete_label.db')

    def setUp(self):
        super().setUp()

    def test_delete_label_successful(self):
        """Verify that a label can be successfully deleted by its ID."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        self.db.delete_label(label_id)
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_label(label_id)
        self.assertEqual(cm.exception.code, "LABEL_NOT_FOUND")

    def test_delete_nonexistent_label(self):
        """Verify that attempting to delete a non-existent label raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.delete_label(9999)
        self.assertEqual(cm.exception.code, "LABEL_NOT_FOUND")

    def test_delete_label_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.delete_label(label_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseClearTaskLabels(BaseTodoDatabaseTest):
    """Test suite for clear_task_labels function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_clear_task_labels.db')

    def setUp(self):
        super().setUp()
    
    def test_clear_task_labels_successful(self):
        """Verify that task labels can be successfully cleared by task ID."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        self.db.link_task_label(task_id, label_id)

        labels = self.db.get_task_labels(task_id)
        self.assertTrue(len(labels) > 0, "No labels found for task")
        self.assertEqual(labels[0][1], self.BASIC_LABEL_TITLE)

        self.db.clear_task_labels(task_id)
        task = self.db.get_task(task_id)
        self.assertEqual(task[4], None)

    def test_clear_task_labels_nonexistent_task(self):
        """Verify that attempting to clear labels for a non-existent task raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.clear_task_labels(9999)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")

    def test_clear_task_labels_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.clear_task_labels(task_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseGetTaskLabels(BaseTodoDatabaseTest):
    """Test suite for get_task_labels function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_get_task_labels.db')

    def setUp(self):
        super().setUp()

    def test_get_task_labels_successful(self):
        """Verify that labels can be successfully retrieved for a task by its ID."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        self.db.link_task_label(task_id, label_id)
        labels = self.db.get_task_labels(task_id)
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0][1], self.BASIC_LABEL_TITLE)

    def test_get_task_labels_nonexistent_task(self):
        """Verify that attempting to retrieve labels for a non-existent task raises DatabaseError."""
        with self.assertRaises(DatabaseError) as cm:
            self.db.get_task_labels(9999)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")

    def test_get_task_labels_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.get_task_labels(task_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseGetAllLabels(BaseTodoDatabaseTest):
    """Test suite for get_all_labels function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_get_all_labels.db')

    def setUp(self):
        super().setUp()

    def test_get_all_labels_successful(self):
        """Verify that all labels can be successfully retrieved."""
        self.db.add_label(self.BASIC_LABEL_TITLE)
        self.db.add_label('test label 2')
        labels = self.db.get_all_labels()
        self.assertEqual(len(labels), 2)

    def test_get_all_labels_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.get_all_labels()
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

class TestTodoDatabaseLinkTaskLabel(BaseTodoDatabaseTest):
    """Test suite for link_task_label function in TodoDatabase class."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_link_task_label.db')

    def setUp(self):
        super().setUp()

    def test_link_task_label_successful(self):
        """Verify that a task and label can be successfully linked."""
        # Create test data
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)

        # Link task and label
        self.db.link_task_label(task_id, label_id)

        # Get linked labels
        labels = self.db.get_task_labels(task_id)

        # Verify results
        self.assertEqual(len(labels), 1, "Expected exactly one label")
        label = labels[0]  # Label format is (id, name, color)
        self.assertEqual(label[0], label_id, "Label ID should match")
        self.assertEqual(label[1], self.BASIC_LABEL_TITLE, "Label name should match")

    def test_link_task_label_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.link_task_label(task_id, label_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")

    def test_link_task_label_duplicate(self):
        """Verify that linking the same task-label pair twice is handled gracefully."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)

        # Link first time
        self.db.link_task_label(task_id, label_id)

        # Link second time should raise LINK_FAILED
        with self.assertRaises(DatabaseError) as cm:
            self.db.link_task_label(task_id, label_id)
        self.assertEqual(cm.exception.code, "LINK_EXISTS")

class TestTodoDatabaseInit(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase.__init__ method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_init.db')

    def setUp(self):
        """Set up test environment."""
        self.TEST_DB_DIR = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_db')
        os.makedirs(self.TEST_DB_DIR, exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        try:
            shutil.rmtree(self.TEST_DB_DIR, ignore_errors=True)
        except Exception:
            pass

    def test_init_creates_directory(self):
        """Verify that __init__ creates database directory if it doesn't exist."""
        test_dir = os.path.join(self.TEST_DB_DIR, 'newdir1')
        test_db = os.path.join(test_dir, 'test.db')
        
        # Ensure clean state
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            
        # Test directory creation
        # skipcq: PYL-W0612
        db = TodoDatabase(test_db)
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.exists(test_db))

        # skipcq: PYL-W0612
        db = TodoDatabase(test_db)
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(os.path.exists(test_db))

    def test_init_creates_tables(self):
        """Verify that __init__ creates all required database tables."""
        with sqlite3.connect(self.TEST_DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Check tasks table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check labels table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='labels'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check task_labels table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_labels'")
            self.assertIsNotNone(cursor.fetchone())

    def test_init_with_env_variable(self):
        """Verify that __init__ uses DB_PATH environment variable when db_file is None."""
        test_db = os.path.join(self.TEST_DB_DIR, 'env_test.db')
        os.environ['DB_PATH'] = test_db
        try:
            db = TodoDatabase(None)
            self.assertEqual(db.db_file, test_db)
        finally:
            del os.environ['DB_PATH']

    def test_init_default_path(self):
        """Verify that __init__ uses default path when no path provided."""
        db = TodoDatabase()
        self.assertEqual(db.db_file, 'todo.db')

    @patch('os.access')
    @patch('os.makedirs')
    def test_init_no_write_permission(self, mock_makedirs, mock_access):
        """Verify that __init__ raises PermissionError when no write permission."""
        mock_access.return_value = False
        mock_makedirs.side_effect = None
        
        with self.assertRaises(PermissionError):
            TodoDatabase(self.TEST_DB_NAME)
        
        mock_access.assert_called_once()

    def test_init_closes_connection(self):
        """Verify that __init__ closes the database connection after initialization."""
        print("DB_NAME: ", self.TEST_DB_NAME)
        db = TodoDatabase(self.TEST_DB_NAME)
        self.assertIsNone(db._conn)

    def test_init_invalid_path_characters(self):
        """Verify that __init__ raises DatabaseError for invalid path characters."""
        invalid_paths = [
            'test<.db',
            'test>.db',
            'test"|.db',
            'test?.db',
            'test&.db'
        ]
        for path in invalid_paths:
            with self.assertRaises(DatabaseError) as cm:
                TodoDatabase(path)
            self.assertEqual(cm.exception.code, "INVALID_PATH")

class TestTodoDatabaseDel(BaseTodoDatabaseTest):
    """Test suite for TodoDatabase.__del__ method."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_del.db')

    def setUp(self):
        self.db = TodoDatabase(self.TEST_DB_NAME)
        super().setUp()

    def tearDown(self):
        if hasattr(self, 'db') and self.db is not None:
            self.db.close()
        super().tearDown()

    def test_del_closes_connection_gracefully(self):
        """Verify that __del__ closes database connection gracefully."""
        # Create a connection explicitly
        conn = sqlite3.connect(self.TEST_DB_NAME)
        self.db._conn = conn

        # Store connection object locally
        test_conn = self.db._conn

        # Delete the database instance
        del self.db
        self.db = None  # Ensure complete cleanup

        # Verify the connection is closed by trying to use it
        with self.assertRaises(sqlite3.ProgrammingError) as cm:
            test_conn.execute("SELECT 1")
        self.assertIn("Cannot operate on a closed database", str(cm.exception))

    @patch('logging.error')
    def test_del_handles_connection_error(self, mock_log_error):
        """Verify that __del__ handles connection errors gracefully."""
        # Create a mock connection that raises an error on close
        mock_conn = Mock()
        mock_conn.close.side_effect = sqlite3.Error("Test error")
        self.db._conn = mock_conn
        
        # Delete the database instance
        del self.db
        
        # Verify error was logged
        mock_log_error.assert_called_once_with(
            "Error closing database connection: %s: %s",
            "Error",
            "Test error"
        )

    def test_del_handles_missing_connection(self):
        """Verify that __del__ handles case when connection doesn't exist."""
        # Ensure no connection exists
        self.db._conn = None
        # This should not raise any exceptions
        del self.db

    def test_del_handles_missing_attribute(self):
        """Verify that __del__ handles case when _conn attribute doesn't exist."""
        # Remove the _conn attribute
        delattr(self.db, '_conn')
        # This should not raise any exceptions
        del self.db
        
class TestTodoDatabaseLogDirectory(BaseTodoDatabaseTest):
    """Test suite for log directory creation functionality."""

    TEST_DB_NAME = os.path.join(BaseTodoDatabaseTest.TEST_DB_DIR, 'test_database_logs.db')

    def setUp(self):
        # Remove log directories if they exist
        self.default_log_dir = "logs"
        self.user_log_dir = os.path.expanduser("~/logs")
        self._cleanup_log_dirs()
        super().setUp()

    def tearDown(self):
        self._cleanup_log_dirs()
        super().tearDown()

    def _cleanup_log_dirs(self):
        """Helper method to clean up log directories."""
        for log_dir in [self.default_log_dir, self.user_log_dir]:
            with suppress(OSError):
                if os.path.exists(log_dir):
                    os.rmdir(log_dir)

    @patch('os.makedirs')
    @patch('logging.FileHandler')  # Add this patch
    def test_default_log_directory_creation(self, mock_file_handler, mock_makedirs):
        """Test that the default logs directory is created."""
        mock_makedirs.side_effect = None
        mock_file_handler.return_value = Mock()
        
        # Patch sys.modules
        modules_patcher = patch.dict('sys.modules', {})
        database_patcher = patch('python.database', create=True)
        
        with modules_patcher, database_patcher:
            from python.database import TodoDatabase # skipcq: PYL-W0404
            TodoDatabase()  # Create instance to trigger directory creation
        
        mock_makedirs.assert_called_with("logs", exist_ok=True)

    @patch('os.makedirs')
    @patch('logging.FileHandler')  # Add this patch
    def test_fallback_log_directory_creation(self, mock_file_handler, mock_makedirs):
        """Test that the fallback user logs directory is created when default fails."""
        user_home = os.path.expanduser("~")
        expected_calls = [
            call("logs", exist_ok=True),
            call(os.path.normpath(os.path.join(user_home, "logs")), exist_ok=True)
        ]
        mock_makedirs.side_effect = [PermissionError, None]
        mock_file_handler.return_value = Mock()
        
        # Create database instance to trigger directory creation
        TodoDatabase()
        
        # Verify both directory creation attempts
        mock_makedirs.assert_has_calls(expected_calls, any_order=False)

    @patch('logging.FileHandler')  # Add this patch
    def test_log_directory_exists_after_init(self, mock_file_handler):
        """Test that at least one log directory exists after initialization."""
        mock_file_handler.return_value = Mock()
        
        # Re-import to trigger directory creation
        with patch.dict('sys.modules'):
            if 'python.database' in sys.modules:
                del sys.modules['python.database']
            from python.database import TodoDatabase  # skipcq: PYL-W0404

        self.assertTrue(
            os.path.exists(self.default_log_dir) or os.path.exists(self.user_log_dir),
            "Neither default nor user log directory exists"
        )

    @patch('os.makedirs')
    @patch('logging.FileHandler')  # Add this patch
    def test_both_directory_creation_fails(self, mock_file_handler, mock_makedirs):
        """Test behavior when both default and fallback directory creation fails."""
        # Setup expected calls
        user_home = os.path.expanduser("~")
        expected_calls = [
            call("logs", exist_ok=True),
            call(os.path.normpath(os.path.join(user_home, "logs")), exist_ok=True)
        ]
        
        # Configure mock to always raise PermissionError
        mock_makedirs.side_effect = PermissionError
        mock_file_handler.return_value = Mock()
        
        # Create database instance - should handle exceptions gracefully
        TodoDatabase()
        
        # Verify both creation attempts were made
        mock_makedirs.assert_has_calls(expected_calls, any_order=False)

class TestDatabaseLogging(BaseTodoDatabaseTest):
    """Test suite for database logging functionality."""

    TEST_DB_NAME = 'test_logging.db'

    def setUp(self):
        super().setUp()
        self.log_file = 'logs/productivity.log'

    def test_operation_logging(self):
        """Test database operation logging"""
        with self.assertLogs(self.db.log, level='DEBUG') as log:
            self.db.add_task("Test Task")
            
            log_output = log.output
            self.assertTrue(any("Database operation" in msg for msg in log_output))
            self.assertTrue(any("[OperationID:" in msg for msg in log_output))
            self.assertTrue(any('"title": "Test Task"' in msg for msg in log_output))

    def test_error_logging(self):
        """Test database error logging"""
        with self.assertLogs(self.db.log, level='ERROR') as log:
            try:
                self.db.get_task(999)
            except DatabaseError:
                pass

            log_output = log.output
            self.assertTrue(any("Task not found" in msg for msg in log_output))
            self.assertTrue(any("[OperationID:" in msg for msg in log_output))

    def test_connection_error_logging(self):
        """Test database connection error logging"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Test error")
            
            with self.assertLogs(self.db.log, level='ERROR') as log:
                try:
                    self.db.add_task("Test Task")
                except DatabaseError:
                    pass

                log_output = log.output
                self.assertTrue(any("Database connection error" in msg for msg in log_output))
                self.assertTrue(any("[OperationID:" in msg for msg in log_output))
