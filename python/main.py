from flask import Flask, jsonify
from todo import TodoList

app = Flask(__name__)
todo = TodoList()

@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(todo.tasks)