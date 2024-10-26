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
        self.assertIn('Task added successfully', output)
        self.assertIn('Buy groceries', output)

    @patch('builtins.input', side_effect=['1', 'Walk dog', '2', '1', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_mark_task_completed(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('[✓]', output)

    @patch('builtins.input', side_effect=['1', 'Old task', '3', '1', 'New task', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_update_task(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn('New task', output)
        self.assertNotIn('Old task', output)

    @patch('builtins.input', side_effect=['1', 'Delete me', '4', '1', '6'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_task(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertNotIn('Delete me', output)

    @patch('builtins.input', side_effect=['5', '6'])
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
