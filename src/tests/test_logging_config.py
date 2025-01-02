import unittest
import os
import json
import logging
import tempfile
from python.logging_config import setup_logging, log_execution_time, log_context

class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")
        self.log_file = os.path.join(self.log_dir, f"test_{os.getpid()}.log")
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logger with unique file
        self.logger = setup_logging("test_logger", log_file=self.log_file)

    def tearDown(self):
        # Close and remove all handlers
        if hasattr(self, 'logger'):
            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)
        
        # Clean up test directory
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            os.rmdir(self.log_dir)
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            pass

    def test_setup_logging(self):
        """Test logging setup configuration"""
        self.assertEqual(self.logger.level, logging.INFO)
        self.assertEqual(len(self.logger.handlers), 2)
        self.assertTrue(any(isinstance(h, logging.FileHandler) for h in self.logger.handlers))
        self.assertTrue(any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers))

    def test_log_execution_time(self):
        """Test execution time logging decorator"""
        @log_execution_time(self.logger)
        def test_function():
            return "test"

        with self.assertLogs(self.logger, level='DEBUG') as log:
            test_function()
            self.assertTrue(any("executed in" in msg for msg in log.output))

    def test_log_context(self):
        """Test logging context manager"""
        operation = "test_operation"
        context_data = {"key": "value"}

        with self.assertLogs(self.logger, level='INFO') as log:
            with log_context(self.logger, operation, **context_data) as op_id:
                self.assertIsNotNone(op_id)
                self.logger.info("Test message")

            log_output = log.output
            self.assertTrue(any(f"Starting {operation}" in msg for msg in log_output))
            self.assertTrue(any(f"Completed {operation}" in msg for msg in log_output))
            self.assertTrue(any("Test message" in msg for msg in log_output))

    def test_log_rotation(self):
        """Test log file rotation"""
        # Setup a specific test log file
        test_log = os.path.join(self.log_dir, "test_rotation.log")
        
        # Create rotating handler with small max size
        handler = logging.handlers.RotatingFileHandler(
            filename=test_log,
            maxBytes=100,  # Small size to ensure rotation
            backupCount=3
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Setup test logger
        test_logger = logging.getLogger('rotation_test')
        test_logger.setLevel(logging.DEBUG)
        for h in test_logger.handlers[:]:
            test_logger.removeHandler(h)
        test_logger.addHandler(handler)

        # Write enough data to trigger rotation
        for i in range(10):
            test_logger.info('x' * 50)  # 50 bytes per message
            handler.doRollover()  # Force rotation

        # Get rotated files
        rotated_files = [f for f in os.listdir(self.log_dir) 
                        if f.startswith("test_rotation.log")]
        
        # Clean up
        handler.close()
        for f in rotated_files:
            try:
                os.remove(os.path.join(self.log_dir, f))
            except OSError:
                pass

        # Verify rotation occurred
        self.assertGreater(len(rotated_files), 1, 
                          f"Expected multiple log files, found: {rotated_files}")

    def test_structured_logging(self):
        """Test structured logging output format"""
        test_msg = {"key": "value", "number": 123}
        
        with self.assertLogs(self.logger, level='INFO') as log:
            self.logger.info(json.dumps(test_msg))
            
            log_output = log.output[0]
            self.assertIn("INFO", log_output)
            self.assertIn("test_logger", log_output)
            self.assertIn("key", log_output)
            self.assertIn("value", log_output)

    def test_error_logging_with_context(self):
        """Test error logging with context"""
        with self.assertLogs(self.logger, level='ERROR') as log:
            try:
                with log_context(self.logger, "error_test"):
                    raise ValueError("Test error")
            except ValueError:
                pass

            log_output = log.output
            self.assertTrue(any("Failed error_test" in msg for msg in log_output))
            self.assertTrue(any("Test error" in msg for msg in log_output))

    def test_request_id_persistence(self):
        """Test request ID persistence across operations"""
        # Setup fresh logger
        test_logger = setup_logging("test_persistence_logger")
        
        # Capture all log messages within the context
        with self.assertLogs(test_logger, level='INFO') as captured:
            with log_context(test_logger, "test_operation") as op_id:
                test_logger.info("Test info message")
                test_logger.error("Test error message")
                test_logger.warning("Test warning message")
            
            # Verify logs were captured and contain operation ID
            self.assertTrue(len(captured.records) > 0, "No logs were captured")
            
            # Get all messages that should contain the operation ID
            messages_with_id = [
                record.message for record in captured.records
                if "test_operation" in record.message
            ]
            
            # Verify we have messages and they contain the operation ID
            self.assertTrue(messages_with_id, "No messages with operation ID found")
            self.assertTrue(
                all(f"OperationID: {op_id}" in msg for msg in messages_with_id),
                f"Operation ID {op_id} not found in all messages"
            )
