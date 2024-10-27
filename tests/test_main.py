import unittest
from unittest.mock import patch
import customtkinter as ctk
from main import TodoListGUI

class TestTodoListGUI(unittest.TestCase):
    def setUp(self):
        self.app = TodoListGUI()
        
    def test_initial_state(self):
        self.assertEqual(len(self.app.todo.tasks), 0)
        self.assertIsInstance(self.app.task_entry, ctk.CTkEntry)
        self.assertIsInstance(self.app.task_listbox, ctk.CTkTextbox)

    def test_add_task(self):
        self.app.task_entry.insert(0, "Test Task")
        self.app.add_task()
        self.assertEqual(len(self.app.todo.tasks), 1)
        self.assertEqual(self.app.todo.tasks[0]["task"], "Test Task")
        
    def test_mark_completed(self):
        # Add a task first
        self.app.task_entry.insert(0, "Complete Me")
        self.app.add_task()
        
        # Simulate selecting the task by setting cursor position
        self.app.task_listbox.mark_set("insert", "1.0")
        
        # Mark the task as completed
        self.app.mark_completed()
        
        # Verify the task is marked as completed
        self.assertTrue(self.app.todo.tasks[0]["completed"])
        
    def test_delete_task(self):
        # First add a task
        self.app.task_entry.insert(0, "Delete Me")
        self.app.add_task()
        initial_count = len(self.app.todo.tasks)
        
        # Simulate task selection by setting cursor position
        self.app.task_listbox.mark_set("insert", "1.0")
        
        # Now delete the task
        self.app.delete_task()
        
        # Verify task was deleted
        self.assertEqual(len(self.app.todo.tasks), initial_count - 1)
        
    def test_update_task(self):
        # Add initial task
        self.app.task_entry.insert(0, "Original Task")
        self.app.add_task()
        
        # Simulate selecting the task
        self.app.task_listbox.mark_set("insert", "1.0")
        
        # Mock the dialog input and update the task
        with patch('customtkinter.CTkInputDialog.get_input', return_value="Updated Task"):
            self.app.update_task()
        
        # Verify the task was updated
        self.assertEqual(self.app.todo.tasks[0]["task"], "Updated Task")
        
    def test_refresh_task_list(self):
        self.app.task_entry.insert(0, "Task 1")
        self.app.add_task()
        self.app.task_entry.insert(0, "Task 2")
        self.app.add_task()
        display_text = self.app.task_listbox.get("1.0", "end-1c")
        self.assertIn("Task 1", display_text)
        self.assertIn("Task 2", display_text)

class TestTodoListGUIEdgeCases(unittest.TestCase):
    def setUp(self):
        self.app = TodoListGUI()
        
    def test_empty_task_add(self):
        initial_count = len(self.app.todo.tasks)
        self.app.add_task()
        self.assertEqual(len(self.app.todo.tasks), initial_count)
        
    def test_mark_completed_empty_list(self):
        self.app.mark_completed()
        self.assertEqual(len(self.app.todo.tasks), 0)        
    def test_delete_from_empty_list(self):
        self.app.delete_task()
        self.assertEqual(len(self.app.todo.tasks), 0)
        
    def test_update_empty_list(self):
        with patch('customtkinter.CTkInputDialog.get_input', return_value="Updated Task"):
            self.app.update_task()
        self.assertEqual(len(self.app.todo.tasks), 0)
        
    def test_multiple_operations(self):
        # Add multiple tasks
        tasks = ["Task 1", "Task 2", "Task 3"]
        for task in tasks:
            self.app.task_entry.insert(0, task)
            self.app.add_task()
        
        # Simulate selecting first task and mark as completed
        self.app.task_listbox.mark_set("insert", "1.0")
        self.app.mark_completed()
        
        # Simulate selecting second task and update it
        self.app.task_listbox.mark_set("insert", "2.0")
        with patch('customtkinter.CTkInputDialog.get_input', return_value="Updated Task"):
            self.app.update_task()
            
        # Simulate selecting third task and delete it
        self.app.task_listbox.mark_set("insert", "3.0")
        self.app.delete_task()
        
        # Verify final task count
        self.assertEqual(len(self.app.todo.tasks), 2)
    def tearDown(self):
        self.app.window.destroy()

if __name__ == '__main__':
    unittest.main()
