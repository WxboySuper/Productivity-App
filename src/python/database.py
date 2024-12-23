import sqlite3
import os
import logging as log
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class DatabaseError(Exception):
    """Custom exception class for database-related errors.

    This exception is raised when database operations fail. Each error is
    associated with a specific error code for better error handling.

    Error codes:
    - TASK_NOT_FOUND: When the requested task doesn't exist
    - INVALID_TITLE: When the task title is None
    - EMPTY_TITLE: When the task title is empty or whitespace
    - INVALID_PRIORITY: When the priority value is not in the valid set
    - DB_CONN_ERROR: When database connection fails
    - DB_QUERY_ERROR: When query execution fails
    - NO_UPDATES: When no valid updates are provided
    - INVALID_VALUE: When a field value has an invalid type

    Example:
        try:
            db.add_task("")
        except DatabaseError as e:
            if e.code == "EMPTY_TITLE":
                print("Task title cannot be empty")
    """
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
            sqlite3.OperationalError: If database connection fails
            PermissionError: If no write permission for database directory
        """
        if db_file is None:
            db_file = os.getenv('DB_PATH', '').strip() or 'todo.db'
        db_dir = os.path.dirname(os.path.abspath(db_file))  
        if not os.path.exists(db_dir):  
            os.makedirs(db_dir, exist_ok=True)  
        if not os.access(db_dir, os.W_OK):  
            raise PermissionError(f"No write permission for database directory: {db_dir}")
        self.db_file = db_file
        # Initialize database but don't keep connection open
        with sqlite3.connect(self.db_file) as conn:
            self.init_database(conn)
        self.db_file = db_file
        self._conn = None

    def __del__(self):
        """Ensures database connection is closed when object is destroyed.

        Any errors during connection closure are logged but not raised,
        as this method is called during garbage collection.
        """
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            log.error("Error closing database connection: %s", e)

    @staticmethod
    def init_database(conn):
        """Initialize database tables if they don't exist."""
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
        cursor.close()

    @staticmethod
    def _validate_priority(priority):
        """Validates the priority value."""
        VALID_PRIORITIES = {
            'ASAP': 0,    # Highest priority
            'HIGH': 1,    # High priority
            'MEDIUM': 2,  # Medium priority
            'LOW': 3,     # Low priority
            'LOWEST': 4   # Lowest priority
        }
        if priority is not None and priority not in VALID_PRIORITIES:
            raise DatabaseError("Invalid priority value", "INVALID_PRIORITY")
        return VALID_PRIORITIES.get(priority)

    @staticmethod
    def _validate_title(title):
        """Validates the task title."""
        if title is None:
            raise DatabaseError("Title cannot be None", "INVALID_TITLE")
        if title.strip() == "":
            raise DatabaseError("Title cannot be empty", "EMPTY_TITLE")

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
            DatabaseError: If there is an error adding the task. Possible error codes:
                - INVALID_PRIORITY: If the priority value is not in a valid set
                - INVALID_TITLE: If the title is None.
                - EMPTY_TITLE: If the title is empty or whitespace.
                - DB_CONN_ERROR: If there is a database connection error.
                - DB_QUERY_ERROR: If there is an error execuring the query.
        """
        self._validate_priority(priority)
        self._validate_title(title)

        query = '''
            INSERT INTO tasks (title, deadline, category, notes, priority)
            VALUES (?, ?, ?, ?, ?)
        '''
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (title, deadline, category, notes, priority))
                conn.commit()
                log.info("Task created successfully with ID %d", cursor.lastrowid)
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

    def _validate_updates(self, updates):
        """Validates and filters update fields."""
        ALLOWED_UPDATES = {
            'title': str,
            'completed': bool,
            'deadline': str,
            'category': str,
            'notes': str,
            'priority': str
        }

        validated_updates = {}
        for field, value in updates.items():
            if field not in ALLOWED_UPDATES:
                continue

            if not isinstance(value, ALLOWED_UPDATES[field]):
                raise DatabaseError(f"Invalid value for field {field}", "INVALID_VALUE")

            if field == 'title':
                self._validate_title(value)
            elif field == 'priority':
                self._validate_priority(value)

            validated_updates[field] = value

        return validated_updates

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
        if not updates:
            raise DatabaseError("No updates provided", "NO_UPDATES")

        validated_updates = self._validate_updates(updates)

        if not validated_updates:
            raise DatabaseError("No valid updates provided", "NO_UPDATES")

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                set_clause = ', '.join(f"{field} = ?" for field in validated_updates)
                #skipcq: BAN-B608
                query = f'UPDATE tasks SET {set_clause} WHERE id = ?'
                values = list(validated_updates.values()) + [task_id]
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

    def mark_completed(self, task_id):
        """
        Marks the task with the specified ID as completed in the database.

        Args:
            task_id (int): The ID of the task to mark as completed.

        Raises:
            DatabaseError: If task not found or database error codes.
        """
        query = 'UPDATE tasks SET completed = TRUE WHERE id = ?'
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_id,))
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def get_task(self, task_id):
        """
        Retrieves a task from the database by its ID.

        Args:
            task_id (int): The ID of the task to retrieve.

        Returns:
            tuple: A tuple containing the task's column values.

        Raises:
            DatabaseError: If the task with the specified ID is not found or database error occurs.
        """
        query = 'SELECT * FROM tasks WHERE id = ?'
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_id,))

                task = cursor.fetchone()
                if task is None:
                    raise DatabaseError(f"Task with ID {task_id} not found", "TASK_NOT_FOUND")

                task_list = list(task)
                task_list[2] = bool(task_list[2])
                return tuple(task_list)
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def get_all_tasks(self):
        """
        Returns all tasks from the database, ordered by creation date in descending order.

        Returns:
            list: A list of tuples, where each tuple represents a task and contains the task's column values.
        """
        query = 'SELECT * FROM tasks ORDER BY created_at DESC'
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def add_label(self, name, color=None):
        """
        Adds a new label to the database or returns existing label ID.

        Args:
            name (str): The name of the label
            color (str, optional): The color code for the label

        Returns:
            int: The ID of the created or existing label

        Raises:
            DatabaseError: If there is an error adding the label. Possible error codes:
                - INVALID_LABEL: If the label name is None
                - EMPTY_LABEL: If the label name is empty or whitespace
                - DB_CONN_ERROR: If database connection fails
                - DB_QUERY_ERROR: If query execution fails
        """
        # Validate label name
        if name is None:
            raise DatabaseError("Label name cannot be None", "INVALID_LABEL")
        if name.strip() == "":
            raise DatabaseError("Label name cannot be empty", "EMPTY_LABEL")

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                # Try to insert the new label
                cursor.execute("""
                    INSERT OR IGNORE INTO labels (name, color)
                    VALUES (?, ?)
                """, (name, color))

                # Get the label_id (whether just inserted or already existed)
                cursor.execute("SELECT id FROM labels WHERE name = ?", (name,))
                result = cursor.fetchone()

                if result:
                    label_id = result[0]
                    log.info("Label operation successful. Label ID: %d", label_id)
                    return label_id

        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            log.error("Error adding label: %s", e)
            raise DatabaseError("An error occurred while adding the label", "DB_QUERY_ERROR") from e

    def get_label(self, label_id):
        """
        Retrieves a label from the database by its ID.

        Args:
            label_id (int): The ID of the label to retrieve.

        Returns:
            tuple: A tuple containing the label's column values.

        Raises:
            DatabaseError: If the label with the specified ID is not found or database error occurs.
        """
        query = 'SELECT * FROM labels WHERE id = ?'
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (label_id,))

                label = cursor.fetchone()
                if label is None:
                    raise DatabaseError(f"Label with ID {label_id} is not found", "LABEL_NOT_FOUND")
                return label
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def delete_label(self, label_id):
        """
        Deletes a label from the database by its ID.

        Args:
            label_id (int): The ID of the label to delete.

        Returns:
            None
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM task_labels WHERE label_id = ?', (label_id,))
                cursor.execute('DELETE FROM labels WHERE id = ?', (label_id,))
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No label found with ID {label_id}", "LABEL_NOT_FOUND")
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def clear_task_labels(self, task_id):
        query = "DELETE FROM task_labels WHERE task_id = ?"

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_id,))
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def get_task_labels(self, task_id):
        """
        Retrieves all labels associated with the specified task.

        Args:
            task_id (int): The ID of the task to retrieve labels for.

        Returns:
            list: A list of tuples, where each tuple represents a label associated with the task.
                Each tuple contains (id, name, color).

        Raises:
            DatabaseError: If database connection fails or task not found.
                Error codes:
                - DB_CONN_ERROR: Database connection error
                - TASK_NOT_FOUND: No task found with given ID
        """
        query = '''
            SELECT l.* FROM labels l
            JOIN task_labels tl ON l.id = tl.label_id
            WHERE tl.task_id = ?
        '''

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                # First check if task exists
                cursor.execute('SELECT id FROM tasks WHERE id = ?', (task_id,))
                if cursor.fetchone() is None:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")

                # Get the labels
                cursor.execute(query, (task_id,))
                return cursor.fetchall()

        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def get_all_labels(self):
        """
        Retrieves all labels from the database.

        Returns:
            list: A list of tuples, where each tuple represents a label and contains the label's ID, name, and color.
        """
        query = 'SELECT * FROM labels'

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def link_task_label(self, task_id, label_id):
        """
        Links a task to a label in the database.

        Args:
            task_id (int): The ID of the task to link to the label.
            label_id (int): The ID of the label to link to the task.

        Raises:
            DatabaseError: With codes:
                - TASK_NOT_FOUND: If task doesn't exist
                - LABEL_NOT_FOUND: If label doesn't exist
                - LINK_EXISTS: If link already exists
                - DB_CONN_ERROR: If database connection fails
        """
        query = 'INSERT INTO task_labels (task_id, label_id) VALUES (?, ?)'

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()

                # Check if task exists
                task = self.get_task(task_id)

                # Check if label exists
                label = self.get_label(label_id)

                try:
                    cursor.execute(query, (task_id, label_id))
                except sqlite3.IntegrityError:
                    raise DatabaseError("Task-label link already exists", "LINK_EXISTS")

        except sqlite3.OperationalError as e:
            log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
