import unittest
from unittest.mock import MagicMock
import customtkinter as ctk
import os
from main import TodoListGUI
from database import TodoDatabase
import sqlite3

class TestTodoDatabase(unittest.TestCase):
    """
    Tests the functionality of the TodoDatabase class, including adding tasks, marking tasks as completed, updating tasks, deleting tasks, and retrieving all tasks.
    
    The TestTodoDatabase class inherits from unittest.TestCase and provides several test methods to verify the behavior of the TodoDatabase class. These tests cover the following aspects:
    
    - Adding a new task with various properties and verifying that the task is correctly added to the database.
    - Marking a task as completed and verifying that the task's `completed` field is set to `True`.
    - Updating an existing task with new properties and verifying that the task is correctly updated in the database.
    - Deleting a task and verifying that the task is no longer present in the database.
    - Clearing any existing tasks, adding two new tasks with different priorities, and verifying that the tasks are correctly retrieved from the database.
    
    These tests help ensure the correct behavior of the TodoDatabase class and its integration with the TodoListGUI class.
    """

    def setUp(self):
        """
        Sets up the test environment by creating a test database instance for the TodoDatabase class.
        """
        self.test_db = "test_todo.db"
        self.db = TodoDatabase(self.test_db)

    def test_add_task(self):
        """
        Tests the `add_task` method of the `TodoDatabase` class by creating a new task with various properties and verifying that the task is correctly added to the database.
        
        Args:
            self (TestTodoDatabase): The instance of the `TestTodoDatabase` class.
        
        Returns:
            None
        """
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
        """
        Tests the `mark_completed` method of the `TodoDatabase` class by creating a new task, marking it as completed, and verifying that the task's `completed` field is set to `True`.
        
        Args:
            self (TestTodoDatabase): The instance of the `TestTodoDatabase` class.
        
        Returns:
            None
        """
        task_id = self.db.add_task("Complete Me")
        self.db.mark_completed(task_id)
        task = self.db.get_task(task_id)
        self.assertTrue(task[2])

    def test_update_task(self):
        """
        Tests the `update_task` method of the `TodoDatabase` class by creating a new task, updating its various properties, and verifying that the task is correctly updated in the database.
        
        Args:
            self (TestTodoDatabase): The instance of the `TestTodoDatabase` class.
        
        Returns:
            None
        """
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
        """
        Tests the `delete_task` method of the `TodoDatabase` class by creating a new task, deleting it, and verifying that the task is no longer present in the database.
        
        Args:
            self (TestTodoDatabase): The instance of the `TestTodoDatabase` class.
        
        Returns:
            None
        """
        task_id = self.db.add_task("Delete Me")
        self.db.delete_task(task_id)
        task = self.db.get_task(task_id)
        self.assertIsNone(task)

    def test_get_all_tasks(self):
        """
        Tests the `get_all_tasks` method of the `TodoDatabase` class by clearing any existing tasks, adding two new tasks with different priorities, and verifying that the tasks are correctly retrieved from the database.
        
        Args:
            self (TestTodoDatabase): The instance of the `TestTodoDatabase` class.
        
        Returns:
            None
        """
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
        """
        Cleans up the test database by deleting the database file after each test.
        
        This method is called after each test in the `TestTodoDatabase` class. It first attempts to delete the instance of the `TodoDatabase` class, and then removes the test database file from the file system. If any errors occur during this process, they are silently ignored.
        """
        try:
            self.db.__del__()
            if os.path.exists(self.test_db):
                os.remove(self.test_db)
        except:
            pass

class TestTodoListGUI(unittest.TestCase):
    """
    Tests the functionality of the TodoListGUI class, including its initial state, the quick_add_task method, the task display format, and the context menu.
    
    The TestTodoListGUI class inherits from unittest.TestCase and provides several test methods to verify the behavior of the TodoListGUI class. These tests cover the following aspects:
    
    - Verifying the initial state of the TodoListGUI class, including the types of the task_entry, task_listbox, and priority_var attributes.
    - Testing the quick_add_task method, which adds a new task to the todo list with the specified title and priority.
    - Checking the formatting of the task display text in the task listbox, ensuring that it includes the expected elements (task title, priority, and category).
    - Verifying the functionality of the context menu, including the "Mark Completed" option.
    
    These tests help ensure the correct behavior of the TodoListGUI class and its integration with the TodoDatabase class.
    """

    def setUp(self):
        """
        Sets up the test environment by creating an instance of the TodoListGUI class.
        
        This method is called before each test in the TestTodoListGUI class. It creates a new instance of the TodoListGUI class and assigns it to the self.app attribute, which can then be used in the test methods.
        """
        self.app = TodoListGUI()

    def test_initial_state(self):
        """
        Tests the initial state of the TodoListGUI class by checking that the task_entry, task_listbox, and priority_var attributes are properly initialized as the expected Customtkinter widget types.
        """
        self.assertIsInstance(self.app.task_entry, ctk.CTkEntry)
        self.assertIsInstance(self.app.task_listbox, ctk.CTkTextbox)
        self.assertIsInstance(self.app.priority_var, ctk.StringVar)

    def test_quick_add_task(self):
        """
        Tests the functionality of the `quick_add_task` method in the `TodoListGUI` class.
        
        This test method verifies that the `quick_add_task` method correctly adds a new task to the `todo` list with the specified title and priority. It first sets the `task_entry` widget to "Test Task", sets the `priority_var` to "1", and then calls the `quick_add_task` method. It then checks that the first task in the `todo.tasks` list has the expected title and priority.
        """
        # Clear the database first
        with sqlite3.connect("todo.db") as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks')
            conn.commit()
            
        self.app.todo.tasks = []
        self.app.task_entry.insert(0, "Test Task")
        self.app.priority_var.set("1")
        
        self.app.window.update()
        self.app.quick_add_task()
        self.app.todo.refresh_tasks()
        self.app.window.update()
        
        task = self.app.todo.tasks[0]
        self.assertEqual(task[1], "Test Task")
        self.assertEqual(task[6], "1")

    def test_task_display_format(self):
        """
        Tests the formatting of task display text in the TodoListGUI application.
        
        This test method verifies that the task display text in the task listbox contains the expected elements, including the task title, priority, and category. It first sets the task entry to "Display Test", sets the priority to "1" and the category to "Work", and then calls the `quick_add_task` method to add the task to the todo list. It then retrieves the display text from the task listbox and checks that it contains the expected elements.
        """
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
        """
        Tests the functionality of the context menu in the TodoListGUI application.

        This test method verifies that the context menu is displayed when the user right-clicks on the task listbox, and that the "Mark Completed" option in the context menu correctly marks the selected task as completed.

        The test first adds a new task with the title "Menu Test" to the todo list, then simulates a right-click event on the task listbox at the coordinates (10, 10). It then calls the `show_context_menu` method to display the context menu, and finally calls the `mark_completed` method to mark the task as completed. The test then checks that the first task in the `todo.tasks` list has its `completed` attribute set to `True`.
        """
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
        """
        Tests the formatting of task display text in the TodoListGUI application.
        
        This test method verifies that the task display text in the task listbox contains the expected elements, including the task title, priority, and category. It first sets the task entry to "Display Test", sets the priority to "1" and the category to "Work", and then calls the `quick_add_task` method to add the task to the todo list. It then retrieves the display text from the task listbox and checks that it contains the expected elements.
        """
        self.app.task_entry.insert(0, "Display Test")
        self.app.priority_var.set("1")
        self.app.category_var.set("Work")
        self.app.quick_add_task()
        display_text = self.app.task_listbox.get("1.0", "end-1c")
        self.assertIn("Display Test", display_text)
        self.assertIn("[1]", display_text)
        self.assertIn("[Work]", display_text)

    def tearDown(self):
        """
        Cleans up the test environment by destroying the application window and removing the todo.db file if it exists.
        
        This method is called after each test case is executed to ensure a clean slate for the next test. It first destroys the application window to close the GUI, then attempts to delete the todo.db file that may have been created during the test. If the file does not exist, the method simply ignores the error.
        """
        self.app.window.destroy()
        try:
            del self.app.todo.db
            if os.path.exists("todo.db"):
                os.remove("todo.db")
        except:
            pass

if __name__ == '__main__':
    unittest.main()
