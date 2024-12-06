import unittest
from unittest.mock import patch
import sqlite3
from datetime import datetime
from src.python.database import TodoDatabase, DatabaseError

class TestTodoDatabase(unittest.TestCase):
    """Test suite for TodoDatabase class functionality."""
    
    # Test database configuration
    TEST_DB_NAME = 'test_todo.db'
    
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

    # Task data for deletion test
    DELETE_TASK_DATA = {
        'title': "Quarterly Report",
        "category": "Work",
        "notes": "Include Q3 Metrics",
        "priority": "2"
    }

    UPDATED_TASK_DATA = {
        'title': 'Updated Task Title',
        'completed': True,
        'category': 'Personal',
        'notes': 'Updated notes',
        'priority': '2'
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

    def setUp(self):
        """Initialize test database before each test case."""
        self.db = TodoDatabase(self.TEST_DB_NAME)
        self.conn = sqlite3.connect(self.TEST_DB_NAME)
        self.db.init_database(self.conn)
    
    # Test Suite for Add Task Functionality
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

    # Test Suite for Delete Task Functionality
    def test_task_delete(self):
        """Verify that a task can be deleted by its ID."""
        deadline_var = datetime.now()
        deadline_str = deadline_var.strftime('%Y-%m-%d %H:%M:%S')
        
        task_data = self.DELETE_TASK_DATA.copy()
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

        with self.assertRaises(ValueError):
            self.db.get_task(task_id)

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

    # Test Suite for Update Task Functionality
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
        self.assertEqual(task[1], updates['title'])
        self.assertEqual(task[2], True)
        self.assertEqual(task[3], updates['deadline'])
        self.assertEqual(task[4], updates['category'])
        self.assertEqual(task[5], updates['notes'])
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
        self.db.update_task(task_id, **updates)
        
        task = self.db.get_task(task_id)
        self.assertEqual(task[1], self.BASIC_TASK_TITLE)
    
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
        

    @patch('sqlite3.connect')
    def test_update_task_db_connection_error(self, mock_connect):
        """Verify that a database connection error during update is handled correctly."""
        mock_connect.side_effect = sqlite3.OperationalError("Unable to connect to the database")
        with self.assertRaises(DatabaseError) as cm:
            self.db.update_task(1, title="New Title")
        self.assertEqual(cm.exception.code, "DB_CONN_ERROR")
    
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