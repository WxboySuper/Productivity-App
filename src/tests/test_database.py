import unittest
from unittest.mock import patch
import sqlite3
from datetime import datetime
from src.python.database import TodoDatabase, DatabaseError
import os
import time
import warnings
from contextlib import suppress

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

    def test_link_task_label_nonexistent_task(self):
        """Verify that attempting to link a task and label with a non-existent task raises DatabaseError."""
        task_id = 9999
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        with self.assertRaises(DatabaseError) as cm:
            self.db.link_task_label(task_id, label_id)
        self.assertEqual(cm.exception.code, "TASK_NOT_FOUND")

    def test_link_task_label_nonexistent_label(self):
        """Verify that attempting to link a task and label with a non-existent label raises DatabaseError."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = 9999
        with self.assertRaises(DatabaseError) as cm:
            self.db.link_task_label(task_id, label_id)
        self.assertEqual(cm.exception.code, "LABEL_NOT_FOUND")

    def test_link_task_label_db_connection_error(self):
        """Verify that a database connection error is handled correctly."""
        task_id = self.db.add_task(self.BASIC_TASK_TITLE)
        label_id = self.db.add_label(self.BASIC_LABEL_TITLE)
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Unable to connect")
            with self.assertRaises(DatabaseError) as cm:
                self.db.link_task_label(task_id, label_id)
            self.assertEqual(cm.exception.code, "DB_CONN_ERROR")