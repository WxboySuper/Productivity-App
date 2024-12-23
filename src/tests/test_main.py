from src.python.main import app
import unittest
from unittest.mock import patch
from datetime import datetime
import json

class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_get_tasks(self):
        """Test GET /tasks endpoint"""
        with patch('src.python.main.todo') as mock_todo:
            # Mock the tasks property with lists instead of tuples
            mock_todo.tasks = [
                [1, "Task 1", None, None, None, None],
                [2, "Task 2", None, "Work", None, 1]
            ]
            
            response = self.app.get('/tasks')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.data), mock_todo.tasks)

    def test_create_task_minimal(self):
        """Test POST /tasks with minimal task data"""
        with patch('src.python.main.todo') as mock_todo:
            mock_todo.add_task.return_value = 1
            
            task_data = {
                'title': 'Test Task'
            }
            
            response = self.app.post('/tasks',
                                   data=json.dumps(task_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 201)
            self.assertEqual(json.loads(response.data), {'id': 1})
            mock_todo.add_task.assert_called_once_with(
                'Test Task',
                deadline=None,
                category=None,
                notes=None,
                priority=None
            )

    def test_create_task_full(self):
        """Test POST /tasks with full task data"""
        with patch('src.python.main.todo') as mock_todo:
            mock_todo.add_task.return_value = 1
            
            deadline = datetime.now().isoformat()
            task_data = {
                'title': 'Test Task',
                'deadline': deadline,
                'category': 'Work',
                'notes': 'Test notes',
                'priority': 1
            }
            
            response = self.app.post('/tasks',
                                   data=json.dumps(task_data),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 201)
            self.assertEqual(json.loads(response.data), {'id': 1})
            mock_todo.add_task.assert_called_once_with(
                'Test Task',
                deadline=deadline,
                category='Work',
                notes='Test notes',
                priority=1
            )

    def test_create_task_invalid_json(self):
        """Test POST /tasks with invalid JSON"""
        response = self.app.post('/tasks',
                               data='invalid json',
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_task_missing_title(self):
        """Test POST /tasks with missing title field"""
        task_data = {
            'category': 'Work'
        }
        
        response = self.app.post('/tasks',
                               data=json.dumps(task_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_create_task_invalid_title_type(self):
        """Test POST /tasks with non-string title"""
        task_data = {
            'title': 123
        }
        
        response = self.app.post('/tasks',
                                data=json.dumps(task_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

    def test_get_tasks_error(self):
        """Test GET /tasks when an error occurs"""
        with patch('src.python.main.todo') as mock_todo:
            # Mock the tasks property to raise an exception
            type(mock_todo).tasks = property(lambda x: (_ for _ in ()).throw(Exception("Test error")))
            
            response = self.app.get('/tasks')
            
            self.assertEqual(response.status_code, 500)
            self.assertEqual(json.loads(response.data), {'error': 'Internal Server Error'})

    def test_create_task_server_error(self):
        """Test POST /tasks when server error occurs"""
        with patch('src.python.main.todo') as mock_todo:
            mock_todo.add_task.side_effect = Exception("Internal error")
            
            task_data = {
                'title': 'Test Task'
            }
            
            response = self.app.post('/tasks',
                                    data=json.dumps(task_data),
                                    content_type='application/json')
            
            self.assertEqual(response.status_code, 500)
            self.assertEqual(json.loads(response.data), {'error': 'Internal server error'})

    def test_create_task_no_data(self):
        """Test POST /tasks with no data scenarios"""
        # Test empty JSON object
        response = self.app.post('/tasks',
                            data=json.dumps({}),
                            content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.data),
            {'error': 'No data provided'}
        )

        # Test missing content type
        response = self.app.post('/tasks', data='')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.data),
            {'error': 'No data provided'}
        )