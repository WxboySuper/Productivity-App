import sys
import json
from python.todo import TodoList
import logging
import uuid
import os
from python.logging_config import setup_logging

os.makedirs("logs", exist_ok=True)

setup_logging(__name__)

log = logging.getLogger(__name__)
todo = TodoList()


def generate_request_id():
    """
    Generate a unique request ID using UUID4.

    Returns:
        str: A unique request ID in string format
    """
    return str(uuid.uuid4())

def handle_command(cmd, payload):
    """
    Process incoming commands and their payloads.

    Args:
        cmd (str): The command to execute ('get_tasks' or 'add_task')
        payload (dict): The command payload containing task details

    Returns:
        dict: Response data depending on the command:
            - For 'get_tasks': List of all tasks
            - For 'add_task': Dictionary with new task_id

    Raises:
        ValueError: If the command is unknown or payload is invalid
    """
    cmd_request_id = generate_request_id()
    log.info("Processing command: %s [RequestID: %s]", cmd, cmd_request_id)
    safe_payload = {k: v for k, v in payload.items() if k not in ['notes', 'personal_info']}  # Add other sensitive fields  
    log.debug("Command payload: %s [RequestID: %s]", json.dumps(safe_payload), cmd_request_id) 

    try:
        if cmd == "get_tasks":
            log.info("Retrieving all tasks [RequestID: %s]", cmd_request_id)
            tasks = todo.tasks
            log.info("Successfully retrieved %d tasks [RequestID: %s]", len(tasks), cmd_request_id)
            return tasks

        if cmd == "add_task":
            if 'title' not in payload or not isinstance(payload['title'], str) or not payload['title'].strip():
                log.error("Missing required fields in payload [RequestID: %s]", cmd_request_id)
                raise ValueError("Missing required fields in payload")

            log.info("Adding new task: %s [RequestID: %s]", payload["title"], cmd_request_id)
            task_id = todo.add_task(
                payload["title"],
                payload.get("deadline"),
                payload.get("category")
            )
            log.info("Successfully added task with ID: %s [RequestID: %s]", task_id, cmd_request_id)
            return {"task_id": task_id}
        log.error("Unknown command received: %s [RequestID: %s]", cmd, cmd_request_id)
        raise ValueError(f"Unknown command: {cmd}")

    except Exception as e:
        log.error("Error processing command %s [RequestID: %s] - Error: %s",
                  cmd, cmd_request_id, str(e), exc_info=True)
        raise

if __name__ == "__main__":
    try:
        request_id = generate_request_id()
        log.info("Bridge script started [RequestID: %s]", request_id)

        if len(sys.argv) != 3:
            log.error("Invalid number of arguments [RequestID: %s]", request_id)
            raise ValueError("Expected 2 arguments: command and payload")

        command = sys.argv[1]
        try:
            data = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            log.error("Invalid JSON payload [RequestID: %s] - Error: %s", request_id, str(e))
            raise

        log.debug("Executing command: %s with payload: %s [RequestID: %s]",
                  command, json.dumps(data), request_id)

        result = handle_command(command, data)
        print(json.dumps(result))
        log.info("Command executed successfully [RequestID: %s]", request_id)

    except Exception as e:
        log.error("Bridge script failed [RequestID: %s] - Error: %s",
                  request_id, str(e), exc_info=True)
        sys.exit(1)
