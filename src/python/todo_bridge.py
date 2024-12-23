import sys
import json
from src.python.todo import TodoList

todo = TodoList()

def handle_command(cmd, payload):
    if cmd == "get_tasks":
        return todo.tasks
    if cmd == "add_tasks":
        return todo.add_task(payload["title"], payload["deadline"], payload["category"])
    # Add more commands as needed

if __name__ == "__main__":
    command = sys.argv[1]  # pragma: no cover
    data = json.loads(sys.argv[2])  # pragma: no cover
    result = handle_command(command, data)  # pragma: no cover
    print(json.dumps(result))  # pragma: no cover
    print(json.dumps(result))  # pragma: no cover
