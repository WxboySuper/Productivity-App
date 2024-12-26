from src.python.database import TodoDatabase, DatabaseError
import logging
import os
import uuid
import json

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S.%f',
    handlers=[
        logging.FileHandler('logs/productivity.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

class TodoList:
    """
    Represents a list of tasks that can be managed, including adding, marking as completed, updating, and deleting tasks.
    The TodoList class uses a TodoDatabase instance to interact with the underlying database for storing and retrieving tasks.

    Attributes:
        db (TodoDatabase): An instance of the TodoDatabase class used to interact with the database.
        tasks (list): A list of tasks,
        where each task is represented as a tuple containing the task ID, task name, deadline, category, notes, and priority.

    Methods:
        refresh_tasks(): Retrieves all tasks from the database and updates the tasks list.
        add_task(task, deadline=None, category=None, notes=None, priority=None): Adds a new task to the database and updates the tasks list.
        mark_completed(task_index): Marks the task at the specified index as completed in the database and updates the tasks list.
        update_task(task_index, **updates): Updates the task at the specified index with the provided updates and saves the changes to the database.
        delete_task(task_index): Deletes the task at the specified index from the database and updates the tasks list.
    """

    def __init__(self, db=None):
        """
        Initializes the TodoList class with a TodoDatabase instance and an empty list of tasks.

        Args:
            db: Optional database instance. If None, creates a new TodoDatabase instance.
        """
        self.db = db if db is not None else TodoDatabase()
        self.tasks = []
        log.info("TodoList initialized with %s", self.db.__class__.__name__)

    def generate_operation_id(self):
        """Generate unique operation ID for tracking."""
        return str(uuid.uuid4())

    def refresh_tasks(self):
        """
        Refreshes the list of tasks by retrieving all tasks
        from the database and updating the `tasks` attribute.

        Raises:
            RuntimeError: If an error occurs while retrieving tasks from the database
        """
        op_id = self.generate_operation_id()
        log.info("Refreshing tasks [OperationID: %s]", op_id)
        
        try:
            self.tasks = self.db.get_all_tasks()
            log.info("Successfully refreshed %d tasks [OperationID: %s]", 
                    len(self.tasks), op_id)
        except TimeoutError as e:
            log.error("Timeout while refreshing tasks [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            self.tasks = []
            raise RuntimeError(f"Connection timeout: {e}") from e
        except DatabaseError as e:
            log.error("Database error while refreshing tasks [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            self.tasks = []
            raise RuntimeError(f"Database error: {str(e)}") from e

    def add_task(self, task, deadline=None, category=None, notes=None, priority=None):
        """
        Adds a new task to the TodoList and saves it to the database.

        Args:
            task (str): The name or description of the new task.
            deadline (datetime.datetime, optional): The deadline for the task. Defaults to None.
            category (str, optional): The category or type of the task. Defaults to None.
            notes (str, optional): Any additional notes or details about the task. Defaults to None.
            priority (int, optional): The priority level of the task, where 1 is the highest priority. Defaults to None.

        Returns:
            int: The ID of the newly added task.
        """
        op_id = self.generate_operation_id()
        log.info("Adding new task [OperationID: %s]", op_id)
        log.debug("Task details [OperationID: %s]: %s", op_id,
                 json.dumps({
                     'task': task,
                     'deadline': str(deadline) if deadline else None,
                     'category': category,
                     'notes': notes,
                     'priority': priority
                 }))

        if not task or not isinstance(task, str):
            log.error("Invalid task parameter [OperationID: %s] - Task must be non-empty string", op_id)
            raise ValueError("Task must be a non-empty string")

        try:
            task_id = self.db.add_task(task, deadline, category, notes, priority)
            self.refresh_tasks()
            log.info("Successfully added task [OperationID: %s, TaskID: %s]", op_id, task_id)
            return task_id
        except (TimeoutError, DatabaseError) as e:
            log.error("Failed to add task [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            raise RuntimeError(f"Database operation failed: {str(e)}") from e

    def mark_completed(self, task_index):
        """
        Marks the task at the specified index as completed in the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to mark as completed.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
            ValueError: If the task is already marked as completed.
        """
        op_id = self.generate_operation_id()
        log.info("Marking task as completed [OperationID: %s, TaskIndex: %d]", 
                op_id, task_index)

        if not (0 <= task_index < len(self.tasks)):
            log.error("Invalid task index [OperationID: %s, TaskIndex: %d]", 
                     op_id, task_index)
            raise IndexError("Invalid task index!")

        task_id = self.tasks[task_index][0]
        try:
            task = self.db.get_task(task_id)
            if task[6]:  # Assuming index 6 stores the completion status
                log.warning("Task is already marked as completed")
                raise ValueError("Task is already marked as completed")

            self.db.mark_completed(task_id)
            self.refresh_tasks()
            log.info("Task marked as completed [OperationID: %s, TaskID: %s]", 
                    op_id, task_id)
        except Exception as e:
            log.error("Failed to mark task as completed [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            raise

    def update_task(self, task_index, **updates):
        """
        Updates the task at the specified index with the provided updates.

        Args:
            task_index (int): The index of the task to update.
            **updates (dict): A dictionary of updates to apply to the task.
            The keys should match the attributes of the task (e.g. 'task', 'deadline', 'category', 'notes', 'priority').

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
            RuntimeError: If a database error or timeout occurs.
        """
        op_id = self.generate_operation_id()
        log.info("Updating task [OperationID: %s, TaskIndex: %d]", op_id, task_index)
        log.debug("Update details [OperationID: %s]: %s", op_id, json.dumps(updates))

        if not (0 <= task_index < len(self.tasks)):
            log.error("Invalid task index [OperationID: %s, TaskIndex: %d]", 
                     op_id, task_index)
            raise IndexError("Invalid task index!")

        task_id = self.tasks[task_index][0]
        try:
            self.db.update_task(task_id, **updates)
            self.refresh_tasks()
            log.info("Successfully updated task [OperationID: %s, TaskID: %s]", 
                    op_id, task_id)
        except Exception as e:
            log.error("Failed to update task [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            raise

    def delete_task(self, task_index):
        """
        Deletes the task at the specified index from the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to delete.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
            RuntimeError: If a database error or timeout occurs.
        """
        op_id = self.generate_operation_id()
        log.info("Deleting task [OperationID: %s, TaskIndex: %d]", op_id, task_index)

        if not (0 <= task_index < len(self.tasks)):
            log.error("Invalid task index [OperationID: %s, TaskIndex: %d]", 
                     op_id, task_index)
            raise IndexError("Invalid task index!")

        task_id = self.tasks[task_index][0]
        try:
            task = self.db.get_task(task_id)
            self.db.delete_task(task_id)
            self.refresh_tasks()
            log.info("Successfully deleted task [OperationID: %s, TaskID: %s]", 
                    op_id, task_id)
        except Exception as e:
            log.error("Failed to delete task [OperationID: %s] - Error: %s", 
                     op_id, str(e), exc_info=True)
            raise
