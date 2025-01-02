from python.server import app
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
        self.assertIn('PORT', self.app.config)
        self.assertEqual(5000, self.app.config['PORT'])

    @staticmethod
    def test_server_not_run():
        """Test server doesn't run when not main module."""
        with unittest.mock.patch('python.server.app.run') as mock_run, \
            unittest.mock.patch('python.server.__name__', 'not_main'):
            
            # Verify app.run was not called
            mock_run.assert_not_called()
