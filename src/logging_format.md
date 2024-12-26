# Python Application Logging Guidelines

## Log Levels (In Order of Severity)

- CRITICAL (50): Application failure requiring immediate action
- ERROR (40): Critical issues that need immediate attention
- WARNING (30): Potentially harmful situations
- INFO (20): General operational events
- DEBUG (10): Detailed information for debugging

## Format Structure

```python
%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]
```

### Components

- levelname: Log level in uppercase
- asctime: Timestamp in ISO format
- name: Logger name (typically module/component)
- message: Log message
- filename: Source file
- lineno: Line number

## Python Configuration

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S.%f',
    handlers=[
        logging.FileHandler('logs/productivity.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)
```

## Usage Examples

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

## Output Examples

```
CRITICAL [2024-01-20 14:30:45.123] task.manager - Task database corrupted [task_manager.py:45]
ERROR [2024-01-20 14:31:12.456] calendar.sync - Calendar sync failed for user: USR123 [calendar_service.py:89]
WARNING [2024-01-20 14:32:00.789] reminder.service - Reminder delivery delayed [reminder_service.py:156]
INFO [2024-01-20 14:33:15.234] task.tracker - Task TAS456 completed [task_tracker.py:78]
```

## Best Practices

1. Use appropriate log levels consistently
2. Include stack traces for errors and critical issues
3. Log structured data when possible (JSON)
4. Include request/correlation IDs for distributed systems
5. Avoid sensitive data (PII, credentials)
6. Use logger.exception() for exception logging
7. Configure log rotation to manage file sizes
