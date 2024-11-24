from flask import Flask, jsonify, request
from todo import TodoList
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

app = Flask(__name__)
todo = TodoList()

@app.route('/tasks', methods=['GET'])
def get_tasks():
    log.info("Handling GET request for all tasks")
    try:
        tasks = todo.tasks
        log.info("successfully retrieved %d tasks", len(tasks))
        return jsonify(tasks)
    except Exception as e:
        log.error("Failed to retrieve tasks: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/tasks', methods=['POST'])
def create_task():
    log.info("Handling POST request to create task")
    try:
        task_data = request.get_json()
        if not task_data:
            log.error("No JSON data received")
            return jsonify({"error": "No data provided"}), 400
        
        if 'title' not in task_data:
            log.error("Missing required field: title")
            return jsonify({"error": "Title is required"}), 400
        
        log.info("Processing task creation", extra={"task_data": task_data})

        task_id = todo.add_task(
            task_data['title'],
            deadline=task_data.get('deadline'),
            category=task_data.get('category'),
            notes=task_data.get('notes'),
            priority=task_data.get('priority')
        )

        log.info("Task created successfully", extra={"task_id": task_id})
        return jsonify({"id": task_id}), 201
    except ValueError as e:
        log.error("Invalid task data: %s", str(e))
        return jsonify({"error": "Invalid task data provided"}), 400
