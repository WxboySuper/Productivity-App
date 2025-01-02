from flask import Flask, jsonify, request
from python.todo import TodoList
from python.logging_config import setup_logging, log_execution_time, log_context
from werkzeug.exceptions import BadRequest
import os
import uuid
import json

os.makedirs("logs", exist_ok=True)
log = setup_logging(__name__)

app = Flask(__name__)
todo = TodoList()

# Startup logging
log.info("Starting Productivity App Server")
log.debug("Initializing with configuration: %s", app.config)

@app.before_request
def before_request():
    request.request_id = str(uuid.uuid4())
    log.info("Incoming %s request to %s [RequestID: %s]",
             request.method, request.path, request.request_id)

@app.route('/tasks', methods=['GET'])
@log_execution_time(log)
def get_tasks():
    with log_context(log, "get_tasks", request_id=request.request_id):
        try:
            tasks = todo.tasks
            log.info("Retrieved %d tasks [RequestID: %s]",
                     len(tasks), request.request_id)
            return jsonify(tasks)
        except Exception as e:
            log.error("Failed to retrieve tasks [RequestID: %s] - Error: %s",
                      request.request_id, str(e), exc_info=True)
            return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/tasks', methods=['POST'])
@log_execution_time(log)
def create_task():
    with log_context(log, "create_task", request_id=request.request_id):
        try:
            if not request.is_json:
                log.warning("Invalid content type or missing data [RequestID: %s]",
                            request.request_id)
                return jsonify({'error': 'No data provided'}), 400

            try:
                task_data = request.get_json()
            except BadRequest:
                log.warning("Invalid JSON or missing data [RequestID: %s]",
                            request.request_id)
                return jsonify({'error': 'No data provided'}), 400

            if not task_data:
                log.warning("No data provided in request [RequestID: %s]",
                            request.request_id)
                return jsonify({'error': 'No data provided'}), 400

            safe_data = {k: v for k, v in task_data.items() if k not in ['notes']}
            log.debug("Received task creation request [RequestID: %s] - Data: %s",
                      request.request_id, json.dumps(safe_data))

            # Validate required fields
            if 'title' not in task_data:
                log.warning("Missing title in task creation [RequestID: %s]",
                            request.request_id)
                raise BadRequest('Missing required field: title')

            # Validate data types
            if not isinstance(task_data['title'], str):
                log.warning("Invalid title type in task creation [RequestID: %s]",
                            request.request_id)
                raise BadRequest('Title must be a string')

            task_id = todo.add_task(
                task_data['title'],
                deadline=task_data.get('deadline'),
                category=task_data.get('category'),
                notes=task_data.get('notes'),
                priority=task_data.get('priority')
            )

            log.info("Successfully created task [RequestID: %s, TaskID: %s]",
                     request.request_id, task_id)
            return jsonify({'id': task_id}), 201

        except BadRequest as e:
            log.warning("Bad request in task creation [RequestID: %s] - Error: %s",
                        request.request_id, str(e))
            return jsonify({'error': 'Bad request'}), 400
        except Exception as e:
            log.error("Failed to create task [RequestID: %s] - Error: %s",
                      request.request_id, str(e), exc_info=True)
            return jsonify({'error': 'Internal Server Error'}), 500

@app.errorhandler(Exception)
def handle_error(error):
    log.error("Unhandled exception [RequestID: %s] - Error: %s",
              getattr(request, 'request_id', 'NO_REQUEST_ID'),
              str(error), exc_info=True)
    return jsonify({'error': 'Internal Server Error'}), 500
