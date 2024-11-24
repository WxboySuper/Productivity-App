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
    log.info("Received GET request for tasks")
    return jsonify(todo.tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    log.info("Received POST request to create a task")
    task_data = request.get_json()
    log.info(f"Received task data: {task_data}")
    task_id = todo.add_task(
        task_data['title'],
        deadline=task_data.get('deadline'),
        category=task_data.get('category'),
        notes=task_data.get('notes'),
        priority=task_data.get('priority')
    )
    log.info(f"Created task with ID: {task_id}")
    return jsonify({'id': task_id}), 201