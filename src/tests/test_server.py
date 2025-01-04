from python.server import app, signal_handler
import unittest
import time
import sqlite3
import os

class TestServer(unittest.TestCase):
    """Test suite for server configuration."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['PORT'] = 5000
        self.app.config['DEBUG'] = False
        self.client = self.app.test_client()
        
        # Register database cleanup
        self.addCleanup(self.cleanup_test_database)

    @staticmethod
    def cleanup_test_database():
        """Remove test database if it exists."""
        try:
            if os.path.exists('productivity.db'):
                os.remove('productivity.db')
        except OSError as e:
            print(f"Warning: Could not remove test database: {e}")

    def tearDown(self):
        """Clean up test environment."""
        self.cleanup_test_database()

    def test_app_exists(self):
        """Verify Flask app exists."""
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        """Verify Flask app is in testing mode."""
        self.assertTrue(self.app.config['TESTING'])

    def test_server_port(self):
        """Verify server port is set to 5000."""
        self.assertIn('PORT', self.app.config)
        self.assertEqual(5000, self.app.config['PORT'])

    def test_health_check_structure(self):
        """Test health check response structure."""
        response = self.client.get('/health')
        data = response.get_json()

        self.assertIn('status', data)
        self.assertIn('uptime_seconds', data)
        self.assertIn('memory', data)
        self.assertIn('system_load', data)
        self.assertIn('database', data)

        # Test memory structure
        self.assertIn('total', data['memory'])
        self.assertIn('available', data['memory'])
        self.assertIn('percent', data['memory'])

        # Test load structure
        self.assertIn('1min', data['system_load'])
        self.assertIn('5min', data['system_load'])
        self.assertIn('15min', data['system_load'])

    def test_health_check_values(self):
        """Test health check returns valid values."""
        response = self.client.get('/health')
        data = response.get_json()

        # Test value types
        self.assertIsInstance(data['uptime_seconds'], (int, float))
        self.assertIsInstance(data['memory']['total'], (int, float))
        self.assertIsInstance(data['memory']['available'], (int, float))
        self.assertIsInstance(data['memory']['percent'], (int, float))
        self.assertIsInstance(data['system_load']['1min'], (int, float))

    @unittest.mock.patch('sqlite3.connect')
    def test_database_health_success(self, mock_connect):
        """Test successful database health check"""
        mock_cursor = unittest.mock.MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        response = self.client.get('/health')
        data = response.get_json()
        
        self.assertEqual(data['database']['status'], 'connected')
        self.assertIsNone(data['database']['error'])
        self.assertIsInstance(data['database']['response_time'], float)
        self.assertEqual(response.status_code, 200)

    @unittest.mock.patch('sqlite3.connect')
    def test_database_health_timeout(self, mock_connect):
        """Test database health check timeout"""
        def slow_connection(*args, **kwargs):
            time.sleep(0.2)  # Simulate slow connection
            return unittest.mock.MagicMock()
            
        mock_connect.side_effect = slow_connection
        
        # Set a very short timeout for the test
        self.app.config['DB_TIMEOUT'] = 0.1
        
        response = self.client.get('/health')
        data = response.get_json()
        
        self.assertEqual(data['database']['status'], 'disconnected')
        self.assertEqual(data['database']['error'], 'Connection timed out')
        self.assertEqual(response.status_code, 503)

    @unittest.mock.patch('sqlite3.connect')
    def test_database_health_error(self, mock_connect):
        """Test database connection error handling"""
        mock_connect.side_effect = sqlite3.OperationalError('test error')
        
        response = self.client.get('/health')
        data = response.get_json()
        
        self.assertEqual(data['database']['status'], 'disconnected')
        self.assertEqual(data['database']['error'], 'Database error: test error')
        self.assertEqual(response.status_code, 503)

    @unittest.mock.patch('sqlite3.connect')
    def test_database_response_time(self, mock_connect):
        """Test database response time measurement"""
        mock_cursor = unittest.mock.MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        response = self.client.get('/health')
        data = response.get_json()
        
        self.assertIsNotNone(data['database']['response_time'])
        self.assertGreater(data['database']['response_time'], 0)
        self.assertLess(data['database']['response_time'], 1000)  # Should be less than 1 second

    @unittest.mock.patch('psutil.virtual_memory')
    @unittest.mock.patch('psutil.getloadavg')
    def test_health_check_degraded(self, mock_load, mock_memory):
        """Test health check degraded status."""
        # Mock high memory usage
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=1000000000,
            percent=95.0
        )
        # Mock high system load
        mock_load.return_value = (6.0, 5.0, 4.0)

        response = self.client.get('/health')
        data = response.get_json()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(data['status'], 'degraded')

    @unittest.mock.patch('psutil.virtual_memory')
    @unittest.mock.patch('psutil.getloadavg')
    def test_health_check_edge_memory(self, mock_load, mock_memory):
        """Test health check with edge case memory values."""
        # Test 100% memory usage
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=0,
            percent=100.0
        )
        mock_load.return_value = (1.0, 1.0, 1.0)  # Normal load
        
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(response.status_code, 503)

        # Test 0% memory usage
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=16000000000,
            percent=0.0
        )
        
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(response.status_code, 200)

    @unittest.mock.patch('psutil.virtual_memory')
    @unittest.mock.patch('psutil.getloadavg')
    def test_health_check_edge_load(self, mock_load, mock_memory):
        """Test health check with edge case load values."""
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=8000000000,
            percent=50.0
        )

        # Test negative load (shouldn't happen in reality, but should handle gracefully)
        mock_load.return_value = (-1.0, -1.0, -1.0)
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(response.status_code, 200)

        # Test extremely high load
        mock_load.return_value = (999.9, 999.9, 999.9)
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(response.status_code, 503)

    @unittest.mock.patch('psutil.virtual_memory')
    @unittest.mock.patch('psutil.getloadavg')
    def test_health_check_custom_thresholds(self, mock_load, mock_memory):
        """Test health check with custom threshold configuration."""
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=8000000000,
            percent=75.0
        )
        mock_load.return_value = (3.0, 3.0, 3.0)

        # Test with custom thresholds
        self.app.config['HEALTH_CHECK_MEMORY_THRESHOLD'] = 80
        self.app.config['HEALTH_CHECK_LOAD_THRESHOLD'] = 4
        
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        
        # Adjust thresholds to trigger degradation
        self.app.config['HEALTH_CHECK_MEMORY_THRESHOLD'] = 70
        self.app.config['HEALTH_CHECK_LOAD_THRESHOLD'] = 2
        
        response = self.client.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'degraded')

    @unittest.mock.patch('psutil.virtual_memory')
    @unittest.mock.patch('psutil.getloadavg')
    @unittest.mock.patch('sqlite3.connect')
    def test_health_check_multiple_degradation(self, mock_connect, mock_load, mock_memory):
        """Test health check with multiple degradation conditions."""
        # Set up all metrics to trigger degradation
        mock_memory.return_value = unittest.mock.Mock(
            total=16000000000,
            available=1000000000,
            percent=95.0
        )
        mock_load.return_value = (10.0, 8.0, 6.0)
        mock_connect.side_effect = sqlite3.OperationalError("test error")

        response = self.client.get('/health')
        data = response.get_json()
        
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(response.status_code, 503)
        self.assertTrue(data['memory']['percent'] > 90)
        self.assertTrue(data['system_load']['1min'] > 5)
        self.assertEqual(data['database']['status'], 'disconnected')

    def test_health_check_uptime(self):
        """Test health check uptime calculation."""
        # Ensure START_TIME is set
        self.app.config['START_TIME'] = time.time() - 10  # 10 seconds ago
        
        response = self.client.get('/health')
        data = response.get_json()

        self.assertGreaterEqual(data['uptime_seconds'], 10)
        self.assertLess(data['uptime_seconds'], 11)  # Allow for small execution time

    @staticmethod
    def test_server_not_run():
        """Test server doesn't run when not main module."""
        with unittest.mock.patch('python.server.app.run') as mock_run, \
            unittest.mock.patch('python.server.__name__', 'not_main'):
            
            # Verify app.run was not called
            mock_run.assert_not_called()

class TestAppContext(unittest.TestCase):
    """Test suite for AppContext functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.context = AppContext(self.app)
        self.cleanup_called = False
        self.count = 0

    def test_register_cleanup(self):
        """Test cleanup handler registration."""
        def cleanup_handler():
            self.cleanup_called = True
        
        self.context.register_cleanup(cleanup_handler)
        self.assertEqual(len(self.context.cleanup_handlers), 1)
        self.context.cleanup()
        self.assertTrue(self.cleanup_called)

    def test_multiple_cleanup_handlers(self):
        """Test multiple cleanup handlers execution."""
        self.count = 0
        
        def handler1():
            self.count += 1
            
        def handler2():
            self.count += 2
            
        self.context.register_cleanup(handler1)
        self.context.register_cleanup(handler2)
        self.context.cleanup()
        self.assertEqual(self.count, 3)

    def test_cleanup_error_handling(self):
        """Test error handling during cleanup."""
        def failing_handler():
            raise Exception("Cleanup failed")
            
        self.context.register_cleanup(failing_handler)
        # Should not raise exception
        self.context.cleanup()

    def test_context_manager(self):
        """Test context manager functionality."""
        self.cleanup_called = False
        
        def cleanup_handler():
            self.cleanup_called = True
            
        self.context.register_cleanup(cleanup_handler)
        
        with self.context:
            pass
            
        self.assertTrue(self.cleanup_called)

    def test_signal_handler(self):
        """Test signal handler triggers cleanup."""
        self.cleanup_called = False
        
        def cleanup_handler():
            self.cleanup_called = True
            
        # Set the global app_context to our test context
        import python.server
        python.server.app_context = self.context
        self.context.register_cleanup(cleanup_handler)
        
        with unittest.mock.patch('sys.exit') as mock_exit:
            signal_handler(signal.SIGTERM, None)
            self.assertTrue(self.cleanup_called)
            mock_exit.assert_called_once_with(0)
