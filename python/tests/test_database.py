import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import sqlite3
from datetime import datetime
from database import TodoDatabase

class TestTodoDatabase(unittest.TestCase):
    def setUp(self):
        self.db = TodoDatabase('test_todo.db')
        self.db.init_database()

    def test_add_task_basic(self):
        task_id = self.db.add_task("Test Task")
        self.assertIsInstance(task_id, int)
        self.assertTrue(task_id > 0)

    def test_add_task_with_all_fields(self):
        print('')
        deadline_var = datetime.now()
        deadline_str = deadline_var.strftime('%Y-%m-%d %H:%M:%S')  # Format for SQLite storage
    
        task_id = self.db.add_task(
            title="Complete Project",
            deadline=deadline_str,
            category="Work",
            notes="Important project deadline",
            priority='1'
        )
    
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
        
        # Convert stored deadline back to datetime for comparison
        self.assertEqual(task[1], "Complete Project")
        self.assertEqual(task[3], deadline_str)
        self.assertEqual(task[4], "Work")
        self.assertEqual(task[5], "Important project deadline")
        self.assertEqual(task[6], '1')

    def test_add_task_with_partial_fields(self):
        task_id = self.db.add_task(
            title="Partial Task",
            category="Personal",
            priority=2
        )
        
        with sqlite3.connect(self.db.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            task = cursor.fetchone()
            
        self.assertEqual(task[1], "Partial Task")
        self.assertIsNone(task[3])  # deadline at index 2
        self.assertEqual(task[4], "Personal")  # category at index 3
        self.assertIsNone(task[5])  # notes at index 4
        self.assertEqual(task[6], '2')

    def test_add_task_empty_title(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task("")

    def test_add_task_none_title(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task(None)

    def test_add_task_invalid_priority(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_task("Test Task", priority=-1)
