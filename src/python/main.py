from flask import Flask, jsonify, request
from src.python.todo import TodoList
from werkzeug.exceptions import BadRequest
import logging as log
import os

os.makedirs("logs", exist_ok=True)

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="logs/todo.log",
)

app = Flask(__name__)
todo = TodoList()

@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        return jsonify(todo.tasks)
    except Exception as e:
        log.error("An error occurred while retrieving tasks: %s", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/tasks', methods=['POST'])
def create_task():
    try:
        task_data = request.get_json(silent=True)
        if not task_data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if 'title' not in task_data:
            raise BadRequest('Missing required field: title')

        # Validate data types
        if not isinstance(task_data['title'], str):
            raise BadRequest('Title must be a string')

        task_id = todo.add_task(
            task_data['title'],
            deadline=task_data.get('deadline'),
            category=task_data.get('category'),
            notes=task_data.get('notes'),
            priority=task_data.get('priority')
        )

        return jsonify({'id': task_id}), 201

    except BadRequest as e:
        log.error("Bad request: %s", str(e))
        return jsonify({'error': 'Internal Server Error'}), 400
    except Exception as e:
        log.error("An error occurred while creating task: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500
