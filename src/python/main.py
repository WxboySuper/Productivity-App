from flask import Flask, jsonify, request
from todo import TodoList

app = Flask(__name__)
todo = TodoList()

@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(todo.tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    task_data = request.get_json()
    print(f"Received task data: {task_data}")  # Debug print
    task_id = todo.add_task(
        task_data['title'],
        deadline=task_data.get('deadline'),
        category=task_data.get('category'),
        notes=task_data.get('notes'),
        priority=task_data.get('priority')
    )
    print(f"Created task with ID: {task_id}")  # Debug print
    return jsonify({'id': task_id}), 201
