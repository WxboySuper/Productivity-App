import unittest
from unittest.mock import patch, MagicMock
import customtkinter as ctk
import os
from main import TodoListGUI
from database import TodoDatabase
import sqlite3

class TestTodoDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_todo.db"
        self.db = TodoDatabase(self.test_db)

    def test_add_task(self):
        task_id = self.db.add_task(
            title="Test Task",
            priority="1",
            deadline="2024-01-01",
            category="Work",
            notes="Test notes"
        )
        task = self.db.get_task(task_id)
        self.assertEqual(task[1], "Test Task")
        self.assertEqual(task[6], "1")

    def test_mark_completed(self):
        task_id = self.db.add_task("Complete Me")
        self.db.mark_completed(task_id)
        task = self.db.get_task(task_id)
        self.assertTrue(task[2])

    def test_update_task(self):
        task_id = self.db.add_task("Original Task")
        updates = {
            "title": "Updated Task",
            "priority": "ASAP",
            "category": "Work",
            "notes": "Updated notes"
        }
        self.db.update_task(task_id, **updates)
        task = self.db.get_task(task_id)
        self.assertEqual(task[1], "Updated Task")
        self.assertEqual(task[6], "ASAP")

    def test_delete_task(self):
        task_id = self.db.add_task("Delete Me")
        self.db.delete_task(task_id)
        task = self.db.get_task(task_id)
        self.assertIsNone(task)

    def test_get_all_tasks(self):
        # Clear existing tasks
        with sqlite3.connect(self.test_db) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks')
            conn.commit()
        
        self.db.add_task("Task 1", priority="1")
        self.db.add_task("Task 2", priority="2")
        tasks = self.db.get_all_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0][6], "1")
        self.assertEqual(tasks[1][6], "2")

    def tearDown(self):
        try:
            self.db.__del__()
            if os.path.exists(self.test_db):
                os.remove(self.test_db)
        except:
            pass

class TestTodoListGUI(unittest.TestCase):
    def setUp(self):
        self.app = TodoListGUI()

    def test_initial_state(self):
        self.assertIsInstance(self.app.task_entry, ctk.CTkEntry)
        self.assertIsInstance(self.app.task_listbox, ctk.CTkTextbox)
        self.assertIsInstance(self.app.priority_var, ctk.StringVar)

    def test_quick_add_task(self):
        self.app.task_entry.insert(0, "Test Task")
        self.app.priority_var.set("1")
        self.app.quick_add_task()
        self.app.todo.refresh_tasks()  # Ensure tasks are refreshed
        task = self.app.todo.tasks[0]
        self.assertEqual(task[1], "Test Task")
        self.assertEqual(task[6], "1")

    def test_task_display_format(self):
        self.app.task_entry.insert(0, "Display Test")
        self.app.priority_var.set("1")
        self.app.category_var.set("Work")
        self.app.quick_add_task()
        self.app.todo.refresh_tasks()  # Ensure tasks are refreshed
        display_text = self.app.task_listbox.get("1.0", "end-1c")
        expected_elements = ["Display Test", "[1]", "Work"]
        for element in expected_elements:
            self.assertIn(element, display_text)

    def test_context_menu(self):
        self.app.task_entry.insert(0, "Menu Test")
        self.app.quick_add_task()
        event = MagicMock()
        event.x = 10
        event.y = 10
        self.app.show_context_menu(event)
        self.app.mark_completed()
        task = self.app.todo.tasks[0]
        self.assertTrue(task[2])

    def test_task_display_format(self):
        self.app.task_entry.insert(0, "Display Test")
        self.app.priority_var.set("1")
        self.app.category_var.set("Work")
        self.app.quick_add_task()
        display_text = self.app.task_listbox.get("1.0", "end-1c")
        self.assertIn("Display Test", display_text)
        self.assertIn("[1]", display_text)
        self.assertIn("[Work]", display_text)

    def tearDown(self):
        self.app.window.destroy()
        try:
            del self.app.todo.db
            if os.path.exists("todo.db"):
                os.remove("todo.db")
        except:
            pass

if __name__ == '__main__':
    unittest.main()
