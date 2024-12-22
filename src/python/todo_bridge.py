import sys
import json
from todo import TodoList

todo = TodoList()

def handle_command(cmd, payload):
    if cmd == "get_tasks":
        return todo.tasks
    if cmd == "add_tasks":
        return todo.add_task(payload["title"], payload["deadline"], payload["category"])
    # Add more commands as needed

if __name__ == "__main__":
    command = sys.argv[1]
    data = json.loads(sys.argv[2])
    result = handle_command(command, data)
    print(json.dumps(result))
    print(json.dumps(result))
