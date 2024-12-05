import sqlite3
from datetime import datetime
import os
import logging as log

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="logs/database.log",
)


class DatabaseError(Exception):
    """Custom exception class for database errors."""
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class TodoDatabase:
    """
    Provides a TodoDatabase class that manages a SQLite database for storing and managing todo tasks.

    The TodoDatabase class handles the initialization of the database,
    creating the necessary tables if they don't already exist.
    It also provides methods for performing CRUD (Create, Read, Update, Delete) operations on tasks and labels,
    as well as methods for managing the relationships between tasks and labels.

    The class uses parameterized SQL queries and input validation to prevent SQL injection vulnerabilities.
    """

    def __init__(self, db_file="todo.db"):
        """
        Initializes a TodoDatabase instance with the specified database file path.

          Raises:
              sqlite3.OperationalError: If the database connection fails or if there are permission issues with the database file.
          """
        if db_file is None:
            db_file = os.getenv('DB_PATH', '').strip() or 'todo.db'
        db_dir = os.path.dirname(os.path.abspath(db_file))  
        if not os.path.exists(db_dir):  
            os.makedirs(db_dir, exist_ok=True)  
        if not os.access(db_dir, os.W_OK):  
            raise PermissionError(f"No write permission for database directory: {db_dir}")
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.init_database()

    def __del__(self):
        """
        Closes the database connection when the TodoDatabase instance is destroyed.

        This method is called automatically when the TodoDatabase instance is garbage collected or explicitly deleted.
        It ensures that the database connection is properly closed, even if an exception occurs during the closing process.
        """
        try:
            self.conn.close()
        except Exception:
            pass

    def init_database(self):
        """
        Initializes the database by creating the necessary tables if they don't already exist.

        This method establishes a connection to the SQLite database file specified in the `self.db_file` attribute. It then creates three tables:

        1. `tasks`: Stores the todo tasks with fields for title, completion status, deadline, category, notes, priority, and creation timestamp.
        2. `labels`: Stores the labels that can be associated with tasks, with fields for name and color.
        3. `task_labels`: A junction table that stores the many-to-many relationship between tasks and labels.

        The method uses parameterized SQL queries to create the tables, which helps prevent SQL injection vulnerabilities.
        If the tables already exist, the method simply skips their creation.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    deadline DATETIME,
                    category TEXT,
                    notes TEXT,
                    priority INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_labels (
                    task_id INTEGER,
                    label_id INTEGER,
                    FOREIGN KEY (task_id) REFERENCES tasks (id),
                    FOREIGN KEY (label_id) REFERENCES labels (id),
                    PRIMARY KEY (task_id, label_id)
                )
            ''')
            conn.commit()

    def add_task(self, title, deadline=None, category=None, notes=None, priority=None):
        """
        Adds a new task to the database.

        Args:
            title (str): The title of the task.
            deadline (str, optional): The deadline of the task.
            category (str, optional): The category of the task.
            notes (str, optional): Additional notes for the task.
            priority (str, optional): The priority of the task.

        Returns:
            int: The ID of the newly created task.

        Raises:
            DatabaseError: If there is an error adding the task.
        """
        query = '''
            INSERT INTO tasks (title, deadline, category, notes, priority)
            VALUES (?, ?, ?, ?, ?)
        '''
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (title, deadline, category, notes, priority))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            log.error("Error adding task: %s", e)
            raise DatabaseError("An error occurred while adding the task", "DB_QUERY_ERROR") from e

    def delete_task(self, task_id):
        """
        Deletes the task with the specified ID from the database.

        Args:
            task_id (int): The ID of the task to delete.

        Raises:
            DatabaseError: If there is an error deleting the task or if the task does not exist.
        """
        query = 'DELETE FROM tasks WHERE id = ?'
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_id,))
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
                conn.commit()
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            log.error("Error deleting task: %s", e)
            raise DatabaseError("An error occurred while deleting the task", "DB_QUERY_ERROR") from e

    def update_task(self, task_id, **updates):
        """
        Updates a task in the database with the provided field updates.

        Args:
            task_id (int): The ID of the task to update.
            **updates (dict): A dictionary of field updates to apply to the task.
                              Allowed fields are `title`, `completed`, `deadline`, `category`, `notes`, and `priority`.

        Raises:
            DatabaseError: If there is an error updating the task.
        """
        ALLOWED_UPDATES = {
            'title': str,
            'completed': bool,
            'deadline': str,
            'category': str,
            'notes': str,
            'priority': str
        }

        VALID_PRIORITIES = {'ASAP', '1', '2', '3', '4'}

        validated_updates = {}
        for field, value in updates.items():
            if field not in ALLOWED_UPDATES:
                continue

            if not isinstance(value, ALLOWED_UPDATES[field]):
                continue

            if field == 'priority' and value not in VALID_PRIORITIES:
                continue

            validated_updates[field] = value

        if not validated_updates:
            return

        query = 'UPDATE tasks SET ' + ', '.join(f'{field} = :{field}' for field in validated_updates) + ' WHERE id = :task_id'
        values = {field: validated_updates[field] for field in validated_updates}
        values['task_id'] = task_id

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
                conn.commit()
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            log.error("Error updating task: %s", e)
            raise DatabaseError("An error occurred while updating the task", "DB_QUERY_ERROR") from e

    def get_task_labels(self, task_id):
        """
        Retrieves all labels associated with the specified task.

        Args:
            task_id (int): The ID of the task to retrieve labels for.

        Returns:
            list: A list of tuples, where each tuple represents a label associated with the task.
                  The tuple contains the label's ID, name, and color.
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.* FROM labels l
                JOIN task_labels tl ON l.id = tl.label_id
                WHERE tl.task_id = ?
            ''', (task_id,))
            return cursor.fetchall()

    def mark_completed(self, task_id):
        """
        Marks the task with the specified ID as completed in the database.

        Args:
            task_id (int): The ID of the task to mark as completed.

        Returns:
            None
        """
        query = 'UPDATE tasks SET completed = TRUE WHERE id = ?'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))

    def get_all_tasks(self):
        """
        Returns all tasks from the database, ordered by creation date in descending order.

        Returns:
            list: A list of tuples, where each tuple represents a task and contains the task's column values.
        """
        query = 'SELECT * FROM tasks ORDER BY created_at DESC'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def get_task(self, task_id):
        """
        Retrieves a task from the database by its ID.

        Args:
            task_id (int): The ID of the task to retrieve.

        Returns:
            tuple: A tuple containing the task's column values.

        Raises:
            ValueError: If the task with the specified ID is not found.
        """
        query = 'SELECT * FROM tasks WHERE id = ?'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
    
            task = cursor.fetchone()
            if task is None:
                raise ValueError(f"Task with ID {task_id} not found")
            return task

    def delete_label(self, label_id):
        """
        Deletes a label from the database by its ID.

        Args:
            label_id (int): The ID of the label to delete.

        Returns:
            None
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM task_labels WHERE label_id = ?', (label_id,))
            cursor.execute('DELETE FROM labels WHERE id = ?', (label_id,))

    def get_all_labels(self):
        """
        Retrieves all labels from the database.

        Returns:
            list: A list of tuples, where each tuple represents a label and contains the label's ID, name, and color.
        """
        query = 'SELECT * FROM labels'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def link_task_label(self, task_id, label_id):
        """
        Links a task to a label in the database.

        Args:
            task_id (int): The ID of the task to link to the label.
            label_id (int): The ID of the label to link to the task.

        Returns:
            None
        """
        query = 'INSERT INTO task_labels (task_id, label_id) VALUES (?, ?)'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id, label_id))
    
    def clear_task_labels(self, task_id):
        query = "DELETE FROM task_labels WHERE task_id = ?"
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(query, (task_id,))

    def add_label(self, name, color=None):
        query = """
        INSERT OR IGNORE INTO labels (name, color)
        VALUES (?, ?)
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(query, (name, color))
            
        # Get the label_id (whether it was just inserted or already existed)
        query = "SELECT id FROM labels WHERE name = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (name,))
        return cursor.fetchone()[0]
