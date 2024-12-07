import unittest
import sqlite3
from datetime import datetime
from src.python.database import TodoDatabase

class TestTodoDatabase(unittest.TestCase):
    """Test suite for TodoDatabase class functionality."""
    
    # Test database configuration
    TEST_DB_NAME = 'test_todo.db'
    
    # Test data constants
    BASIC_TASK_TITLE = "Test Task"
    
    # Full task data
    FULL_TASK_DATA = {
        'title': "Complete Project",
        'category': "Work",
        'notes': "Important project deadline",
        'priority': 1
    }
    
    # Partial task data
    PARTIAL_TASK_DATA = {
        'title': "Partial Task",
        'category': "Personal",
        'priority': 2
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
    INVALID_PRIORITY = -1

    def setUp(self):
        """Initialize test database before each test case."""
        self.db = TodoDatabase(self.TEST_DB_NAME)
        self.db.init_database()
    
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
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task("")

    def test_add_task_none_title(self):
        """Verify that None task titles are rejected."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task(None)

    def test_add_task_invalid_priority(self):
        """Verify that invalid priority values are rejected."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task(self.BASIC_TASK_TITLE, priority=self.INVALID_PRIORITY)
