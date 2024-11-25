import unittest
import sqlite3
from datetime import datetime
from ..python.database import TodoDatabase
import os

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
        'title': 'title',
        'deadline': 'deadline',
        'category': 'category',
        'notes': 'notes',
        'priority': 'priority'
    }

    
    # Invalid data
    INVALID_PRIORITY = -1

    def setUp(self):
        """Initialize test database before each test case."""
        self.db = TodoDatabase(self.TEST_DB_NAME)
        self.db.init_database()

    def tearDown(self):
        """Clean up test database after each test."""
        if os.path.exists(self.TEST_DB_NAME):
            os.remove(self.TEST_DB_NAME)
    
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
    
        task_id = self.db.add_task(**task_data)
    
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
        
        self.assertEqual(task[self.FIELD_MAPPING['title']], self.FULL_TASK_DATA['title'])
        self.assertEqual(task[self.FIELD_MAPPING['deadline']], deadline_str)
        self.assertEqual(task[self.FIELD_MAPPING['category']], self.FULL_TASK_DATA['category'])
        self.assertEqual(task[self.FIELD_MAPPING['notes']], self.FULL_TASK_DATA['notes'])
        self.assertEqual(task[self.FIELD_MAPPING['priority']], self.FULL_TASK_DATA['priority'])

    def test_add_task_with_partial_fields(self):
        """Verify task creation with only some fields populated."""
        task_id = self.db.add_task(**self.PARTIAL_TASK_DATA)
        
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
            
        self.assertEqual(task[self.task_dict['title'], self.PARTIAL_TASK_DATA['title']])
        self.assertIsNone(task[self.task_dict['deadline']])
        self.assertEqual(task[self.task_dict['category']], self.PARTIAL_TASK_DATA['category'])
        self.assertIsNone(task[self.task_dict['notes']])
        self.assertEqual(task[self.task_dict['priority']], self.PARTIAL_TASK_DATA['priority'])

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
