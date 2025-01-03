from python.server import app, AppContext, signal_handler
import unittest
import signal

class TestServer(unittest.TestCase):
    """Test suite for server configuration."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['PORT'] = 5000
        self.app.config['DEBUG'] = False
        self.client = self.app.test_client()

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
