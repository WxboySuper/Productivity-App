import sys
import json
from todo import TodoList

todo = TodoList()

def handle_command(command, data):
    if command == "get_tasks":
        return todo.tasks
    elif command == "add_tasks":
        return todo.add_task(data["title"], data["deadline"], data["category"])
    # Add more commands as needed

if __name__ == "__main__":
    command = sys.argv[1]
    data = json.loads(sys.argv[2])
    result = handle_command(command, data)
    print(json.dumps(result))