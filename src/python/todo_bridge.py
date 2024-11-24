import sys
import json
from todo import TodoList
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

todo = TodoList()

def handle_command(cmd, payload):
    if cmd == "get_tasks":
        log.info("Received get_tasks command")
        return todo.tasks
    elif cmd == "add_tasks":
        log.info("Received add_tasks command with title: %s", payload["title"])
        return todo.add_task(payload["title"], payload["deadline"], payload["category"])
    else:
        log.warning("Received unknown command: %s", cmd)
    # Add more commands as needed

if __name__ == "__main__":
    log.info('Bridge started')
    command = sys.argv[1]
    data = json.loads(sys.argv[2])
    result = handle_command(command, data)
    print(json.dumps(result))
    print(json.dumps(result))