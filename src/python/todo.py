from src.python.database import TodoDatabase
import logging as log
import os

os.makedirs("logs", exist_ok=True)

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="logs/todo.log",
)


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

    def refresh_tasks(self):
        """Refreshes the list of tasks by retrieving all tasks from the database and updating the `tasks` attribute."""
        self.tasks = self.db.get_all_tasks()

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
        task_id = self.db.add_task(task, deadline, category, notes, priority)
        self.refresh_tasks()
        log.info("Task '%s' added successfully!", task)
        return task_id

    def mark_completed(self, task_index):
        """
        Marks the task at the specified index as completed in the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to mark as completed.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            self.db.mark_completed(task_id)
            self.refresh_tasks()
            log.info("Task marked as completed!")
        else:
            log.error("Invalid task index!")
            raise IndexError("Invalid task index!")

    def update_task(self, task_index, **updates):
        """
        Updates the task at the specified index with the provided updates.

        Args:
            task_index (int): The index of the task to update.
            **updates (dict): A dictionary of updates to apply to the task.
            The keys should match the attributes of the task (e.g. 'task', 'deadline', 'category', 'notes', 'priority').

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            self.db.update_task(task_id, **updates)
            self.refresh_tasks()
            print("Task updated successfully!")
        else:
            log.error("Invalid task index!")
            raise IndexError("Invalid task index!")

    def delete_task(self, task_index):
        """
        Deletes the task at the specified index from the database and updates the tasks list.

        Args:
            task_index (int): The index of the task to delete.

        Raises:
            IndexError: If the `task_index` is out of range for the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            task = self.db.get_task(task_id)
            self.db.delete_task(task_id)
            self.refresh_tasks()
            print(f"Task '{task[1]}' deleted successfully!")
        else:
            log.error("Invalid task index!")
            raise IndexError("Invalid task index!")
