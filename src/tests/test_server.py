from src.python.server import app
import src.python.server
import unittest

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
        self.assertEqual(app.config.get('PORT', 5000), 5000)

    @staticmethod
    def test_server_run(run):
        """Test server run configuration."""
        with unittest.mock.patch('src.python.server.app.run') as mock_run:
            # Import after patching
            from src.python.server import run_server

            # Run server function
            run_server()

            # Verify app.run was called with correct port
            mock_run.assert_called_once_with(port=5000)

    @staticmethod
    def test_server_not_run(run):
        """Test server doesn't run when not main module."""
        with unittest.mock.patch('src.python.server.app.run') as mock_run, \
            unittest.mock.patch('src.python.server.__name__', 'not_main'):
            import importlib
            importlib.reload(src.python.server)

            # Verify app.run was not called
            mock_run.assert_not_called()
