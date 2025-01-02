# Application Logging Guidelines

## Python Logging Configuration

### Log Levels (In Order of Severity)

- CRITICAL (50): Application failure requiring immediate action
- ERROR (40): Critical issues that need immediate attention
- WARNING (30): Potentially harmful situations
- INFO (20): General operational events
- DEBUG (10): Detailed information for debugging

### Format Structure

```python
%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]
```

#### Components

- levelname: Log level in uppercase
- asctime: Timestamp in ISO format
- name: Logger name (typically module/component)
- message: Log message
- filename: Source file
- lineno: Line number

### Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S.%f',
    handlers=[
        logging.FileHandler('logs/productivity.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)
```

**Logging level DEBUG used during troubleshooting, otherwise INFO is default in the codebase.**

### Usage Examples

```python
# Critical - Application breaking issues
logger.critical("Task database corrupted - Unable to load user tasks")
logger.critical("Configuration file missing - Essential settings unavailable")

# Error - Component failure
logger.error("Failed to save task: %s for user: %s", task_id, user_id)
logger.error("Calendar sync failed - Unable to update scheduled items")

# Warning - Notable issues
logger.warning("User %s exceeded daily task limit", user_id)
logger.warning("Reminder service experiencing delays > 5 minutes")

# Info - General flow
logger.info("Task %s marked as complete by user %s", task_id, user_id)
logger.info("New productivity goal created: %s", goal_name)

# Debug - Detailed information
logger.debug("Task priority recalculation for user %s", user_id)
logger.debug("Cache refresh triggered for dashboard widgets")
```

### Output Examples

```
CRITICAL [2024-01-20 14:30:45.123] task.manager - Task database corrupted [task_manager.py:45]
ERROR [2024-01-20 14:31:12.456] calendar.sync - Calendar sync failed for user: USR123 [calendar_service.py:89]
WARNING [2024-01-20 14:32:00.789] reminder.service - Reminder delivery delayed [reminder_service.py:156]
INFO [2024-01-20 14:33:15.234] task.tracker - Task TAS456 completed [task_tracker.py:78]
```

## JavaScript Logging Configuration

### Format Structure
### Format Structure

```javascript
{
    "requestId": "req_xyz123",
    "operation": "operationName",
    "timestamp": "2024-01-20T14:30:45.123Z",
    "details": {
        // Operation-specific details
    },
    "error": {  // Optional, present only for errors
        "message": "Error message",
        "stack": "Error stack trace"
    }
}
```

#### Components

- requestId: Unique identifier for the operation
- operation: Name of the logged operation
- timestamp: ISO 8601 formatted date and time
- details: Object containing operation-specific information
- error: Optional error information including message and stack trace

### Configuration
```javascript
const log = require('electron-log');

// File logging configuration
log.transports.file.level = 'info';
log.transports.file.maxSize = 10 * 1024 * 1024; // 10MB
log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}';
log.transports.file.fileName = 'productivity.log';

// Console logging configuration
log.transports.console.level = 'debug';
```

### Usage Examples
```javascript
// Operation logging with request tracking
logOperation('debug', 'fetchData', { url: '/api/data' });
logOperation('info', 'taskCreated', { taskId: 123 });
logOperation('warn', 'retryAttempt', { attempt: 2 });
logOperation('error', 'requestFailed', { url: '/api/data' }, error);

// Direct logging
log.info('Application started');
log.error('Failed to connect', error);
```

### Output Examples

```javascript
// Debug output
[2024-01-20 14:30:45.123] [debug] {
    "requestId": "req_4f8d3c2",
    "operation": "fetchData",
    "timestamp": "2024-01-20T14:30:45.123Z",
    "details": {
        "url": "/api/tasks",
        "method": "GET"
    }
}

// Info output
[2024-01-20 14:31:12.456] [info] {
    "requestId": "req_9a7b6c5",
    "operation": "taskCreated",
    "timestamp": "2024-01-20T14:31:12.456Z",
    "details": {
        "taskId": 123,
        "title": "New Task"
    }
}

// Warning output
[2024-01-20 14:32:00.789] [warn] {
    "requestId": "req_2e4f6d8",
    "operation": "fetchRetry",
    "timestamp": "2024-01-20T14:32:00.789Z",
    "details": {
        "attempt": 2,
        "url": "/api/tasks"
    }
}

// Error output
[2024-01-20 14:33:15.234] [error] {
    "requestId": "req_1a2b3c4",
    "operation": "requestFailed",
    "timestamp": "2024-01-20T14:33:15.234Z",
    "details": {
        "url": "/api/tasks"
    },
    "error": {
        "message": "Failed to fetch tasks: Network error",
        "stack": "Error: Failed to fetch tasks\n    at fetchTasks (/src/renderer.js:45:15)\n    at processRequest (/src/main.js:123:22)"
    }
}
```

### Common Scenarios

```javascript
// API Request Logging
logOperation('debug', 'apiRequest', {
    url: '/api/tasks',
    method: 'GET',
    parameters: { limit: 10 }
});

// Task Operation Logging
logOperation('info', 'taskOperation', {
    operation: 'create',
    taskId: 123,
    taskTitle: 'New Task'
});

// Error Handling
logOperation('error', 'databaseError', {
    operation: 'insert',
    table: 'tasks'
}, new Error('Database connection failed'));

// Performance Monitoring
logOperation('debug', 'performanceMetric', {
    operation: 'taskLoad',
    duration: 235,
    taskCount: 50
});
```

## Cross-Platform Integration

### Shared Log File
Both Python and JavaScript components write to:
```
/logs/productivity.log
```

### Log Levels
- CRITICAL/ERROR (Python) = error (JavaScript)
- WARNING (Python) = warn (JavaScript)
- INFO (Python) = info (JavaScript)
- DEBUG (Python) = debug (JavaScript)

### Request Tracking
- Python: Uses UUID4 for operation IDs
- JavaScript: Uses base36 random strings with 'req_' prefix
- Both platforms include request/operation IDs in all logs

### Performance Logging
- Python: Uses @log_execution_time decorator
- JavaScript: Includes timing in operation details

## Best Practices

1. Use appropriate log levels consistently across platforms
2. Include operation/request IDs for all logs
3. Use structured logging (JSON) for machine-readable logs
4. Include contextual information in log messages
5. Log all errors with stack traces
6. Use rotation to manage log file sizes
7. Avoid sensitive data in logs
8. Use consistent timestamp format (ISO 8601)
9. Include source context (file, line) where available
10. Log start/end of important operations

## Error Handling

### Python Errors
```python
try:
    operation()
except Exception as e:
    log.error("Operation failed - Error: %s", str(e), exc_info=True)
```

### JavaScript Errors
```javascript
try {
    await operation()
} catch (error) {
    logOperation('error', 'operationFailed', {}, error)
}
```
