from database import TodoDatabase, DatabaseError
from logging_config import setup_logging, log_execution_time, log_context
import os
import uuid
import json
from typing import List, Optional
import logging

os.makedirs("logs", exist_ok=True)

log = setup_logging(__name__)


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

    @staticmethod
    def generate_operation_id():
        """Generate unique operation ID for tracking."""
        return str(uuid.uuid4())

    @log_execution_time(log)
    def refresh_tasks(self):
        """
        Retrieves all tasks from the database and updates the tasks list.

        This method fetches the latest state of tasks from the database and updates
        the internal tasks list. It ensures the TodoList instance has the most
        up-to-date information.

        Raises:
            RuntimeError: If a database error or timeout occurs during the refresh operation.
        """
        with log_context(log, "refresh_tasks", operation_id=self.generate_operation_id()):
            try:
                self.tasks = self.db.get_all_tasks()
                log.info("Successfully refreshed %d tasks", len(self.tasks))
            except (TimeoutError, DatabaseError) as e:
                log.error("Failed to refresh tasks: %s", str(e))
                self.tasks = []
                raise RuntimeError(f"Database operation failed: {str(e)}") from e

    @log_execution_time(log)
    def add_task(self, title: str, deadline: Optional[str] = None, 
                 category: Optional[str] = None, priority: Optional[str] = None) -> dict:
        """Add a new task to the todo list."""
        try:
            with self.db.transaction() as cursor:
                cursor.execute(
                    """INSERT INTO tasks (title, deadline, category, priority, completed)
                       VALUES (?, ?, ?, ?, ?) RETURNING id, title, deadline, category, 
                       priority, completed""",
                    (title, deadline, category, priority, False)
                )
                row = cursor.fetchone()
                return {
                    'id': row[0],
                    'title': row[1],
                    'deadline': row[2],
                    'category': row[3],
                    'priority': row[4],
                    'completed': bool(row[5])
                }
        except Exception as e:
            log.error("Failed to add task: %s", str(e))
            raise

    @log_execution_time(log)
    def mark_completed(self, task_index):
        """
        Marks the task at the specified index as completed in the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to mark as completed.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
            ValueError: If the task is already marked as completed.
            RuntimeError: If a database error or timeout occurs.
        """
        with log_context(log, "mark_completed", operation_id=self.generate_operation_id()):
            if not 0 <= task_index < len(self.tasks):
                log.error("Invalid task index [TaskIndex: %d]", task_index)
                raise IndexError("Invalid task index!")

            task_id = self.tasks[task_index][0]
            try:
                task = self.db.get_task(task_id)
                if task[6]:  # Assuming index 6 stores the completion status
                    log.warning("Task is already marked as completed")
                    raise ValueError("Task is already marked as completed")

                try:
                    self.db.mark_completed(task_id)
                    self.refresh_tasks()
                    log.info("Task marked as completed [TaskID: %s]", task_id)
                except (TimeoutError, DatabaseError) as e:
                    error_msg = str(e)
                    log.error("Failed to mark task as completed - Error: %s", error_msg, exc_info=True)
                    raise RuntimeError(f"Database operation failed: {error_msg}") from e
            except (TimeoutError, DatabaseError) as e:
                error_msg = str(e)
                log.error("Failed to get task details - Error: %s", error_msg, exc_info=True)
                raise RuntimeError(f"Database operation failed: {error_msg}") from e

    @log_execution_time(log)
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
        with log_context(log, "update_task", operation_id=self.generate_operation_id()):
            # Create a copy of updates for logging with datetime converted to string
            log_updates = updates.copy()
            if 'deadline' in log_updates and log_updates['deadline'] is not None:
                log_updates['deadline'] = str(log_updates['deadline'])

            log.debug("Update details: %s", json.dumps(log_updates))

            if not 0 <= task_index < len(self.tasks):
                log.error("Invalid task index [TaskIndex: %d]", task_index)
                raise IndexError("Invalid task index!")

            task_id = self.tasks[task_index][0]
            try:
                self.db.update_task(task_id, **updates)
                self.refresh_tasks()
                log.info("Successfully updated task [TaskID: %s]", task_id)
            except (TimeoutError, DatabaseError) as e:
                error_msg = str(e)
                log.error("Failed to update task - Error: %s", error_msg, exc_info=True)
                raise RuntimeError(f"Database operation failed: {error_msg}") from e

    @log_execution_time(log)
    def delete_task(self, task_index):
        """
        Deletes the task at the specified index from the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to delete.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
            RuntimeError: If a database error or timeout occurs.
        """
        with log_context(log, "delete_task", operation_id=self.generate_operation_id()):
            if not 0 <= task_index < len(self.tasks):
                log.error("Invalid task index [TaskIndex: %d]", task_index)
                raise IndexError("Invalid task index!")

            task_id = self.tasks[task_index][0]
            try:
                self.db.delete_task(task_id)
                self.refresh_tasks()
                log.info("Successfully deleted task [TaskID: %s]", task_id)
            except (TimeoutError, DatabaseError) as e:
                error_msg = str(e)
                log.error("Failed to delete task - Error: %s", error_msg, exc_info=True)
                raise RuntimeError(f"Database operation failed: {error_msg}") from e

    @log_execution_time(log)
    def get_tasks(self) -> List[dict]:
        """Get all tasks from the todo list."""
        try:
            with self.db.transaction() as cursor:
                cursor.execute(
                    """SELECT id, title, deadline, category, priority, completed 
                       FROM tasks ORDER BY id DESC"""
                )
                return [{
                    'id': row[0],
                    'title': row[1],
                    'deadline': row[2],
                    'category': row[3],
                    'priority': row[4],
                    'completed': bool(row[5])
                } for row in cursor.fetchall()]
        except Exception as e:
            log.error("Failed to get tasks: %s", str(e))
            raise
