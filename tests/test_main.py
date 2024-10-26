import unittest
from unittest.mock import patch
from io import StringIO
from main import main

class TestMain(unittest.TestCase):
    @patch('builtins.input', side_effect=['1', 'Buy groceries', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_add_task(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Task 'Buy groceries' added successfully!", output)
        self.assertIn('Buy groceries', output)
    @patch('builtins.input', side_effect=['1', 'Walk dog', '2', '0', '5', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_mark_task_completed(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('[✓]', output)

    @patch('builtins.input', side_effect=['1', 'Old task', '3', '0', 'New task', '5', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_update_task(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        # Check that the final display shows the new task
        final_display = output.split('=== Todo List ===')[-1]
        self.assertIn('New task', final_display)
        self.assertNotIn('Old task', final_display)
    @patch('builtins.input', side_effect=['1', 'Delete me', '4', '0', '5', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_task(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Task 'Delete me' deleted successfully!", output)
        # Add display tasks command to verify the task list is empty
        self.assertIn("No tasks in the list!", output)

    @patch('builtins.input', side_effect=['1', 'Test Task', '5', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_tasks(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('=== Todo List ===', output)

    @patch('builtins.input', side_effect=['7', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_choice(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('Invalid choice', output)

    @patch('builtins.input', side_effect=['6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_exit_application(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('Goodbye!', output)
