import sqlite3
import os
import logging
import json
import uuid


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
    """Database management class for todo tasks."""

    def __init__(self, db_file="todo.db"):
        """Initialize database connection and set up logging."""
        # Set up log directories
        self.default_log_dir = "logs"
        self.user_log_dir = os.path.join(os.path.expanduser("~"), "logs")
        self.log_dir = None

        # Try default directory first
        try:
            os.makedirs(self.default_log_dir, exist_ok=True)
            self.log_dir = self.default_log_dir
        except PermissionError:
            # Try user's home directory as fallback
            try:
                os.makedirs(self.user_log_dir, exist_ok=True)
                self.log_dir = self.user_log_dir
            except PermissionError:
                # If both fail, use current directory
                self.log_dir = "."

        # Set up logging
        log_file_path = os.path.join(self.log_dir, 'productivity.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S.%f',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler()
            ]
        )
        self.log = logging.getLogger(__name__)

        # Initialize database
        if db_file is None:
            db_file = os.getenv('DB_PATH', 'todo.db')

        # Validate database path
        invalid_chars = '<>"|?*&'
        if any(char in str(db_file) for char in invalid_chars):
            self.log.error("Invalid characters in database path: %s",
                           [c for c in str(db_file) if c in invalid_chars])
            raise DatabaseError("Invalid characters in database path", "INVALID_PATH")

        self.db_file = db_file
        db_dir = os.path.dirname(os.path.abspath(db_file))

        try:
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            if not os.access(db_dir, os.W_OK):
                self.log.error("No write permission for database directory: %s", db_dir)
                raise PermissionError(f"No write permission for database directory: {db_dir}")

            with sqlite3.connect(self.db_file) as conn:
                self.init_database(conn)
                self.log.info("Database initialized successfully at %s", self.db_file)
        except Exception as e:
            self.log.error("Failed to initialize database: %s", str(e), exc_info=True)
            raise

        self._conn = None

    def __del__(self):
        """Ensures database connection is closed when object is destroyed.

        Any errors during connection closure are logged but not raised,
        as this method is called during garbage collection.
        """
        try:
            if hasattr(self, '_conn') and self._conn:
                self._conn.close()
                self._conn = None
        except Exception as e:
            logging.error("Error closing database connection: %s: %s",
                          type(e).__name__, str(e))

    @staticmethod
    def generate_operation_id():
        """Generate unique operation ID for tracking."""
        return str(uuid.uuid4())

    def _log_operation(self, operation, details, op_id):
        """Log database operation with structured details."""
        self.log.debug("Database operation [OperationID: %s] - %s: %s",
                       op_id, operation, json.dumps(details))

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
        """Add a new task to the database."""
        op_id = self.generate_operation_id()
        self._log_operation("add_task", {
            "title": title,
            "deadline": str(deadline) if deadline else None,
            "category": category,
            "notes": notes,
            "priority": priority
        }, op_id)

        try:
            self._validate_priority(priority)
            self._validate_title(title)

            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (title, deadline, category, notes, priority)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, deadline, category, notes, priority))
                task_id = cursor.lastrowid
                self.log.info("Task created successfully [OperationID: %s, TaskID: %d]",
                              op_id, task_id)
                return task_id
        except sqlite3.OperationalError as e:
            self.log.error("Database connection error [OperationID: %s]: %s", op_id, str(e))
            raise DatabaseError("Database connection error", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            self.log.error("Error adding task: %s", e)
            raise DatabaseError("An error occurred while adding the task", "DB_QUERY_ERROR") from e
        except Exception as e:
            self.log.error("Failed to add task [OperationID: %s] - Error: %s",
                           op_id, str(e), exc_info=True)
            raise

    def delete_task(self, task_id):
        """
        Deletes the task with the specified ID from the database.

        Args:
            task_id (int): The ID of the task to delete.

        Raises:
            DatabaseError: If there is an error deleting the task or if the task does not exist.
        """
        query = 'DELETE FROM tasks WHERE id = ?'
        op_id = self.generate_operation_id()
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (task_id,))
                if cursor.rowcount == 0:
                    self.log.warning("Task not found [OperationID: %s, TaskID: %d]", op_id, task_id)
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
                conn.commit()
        except sqlite3.OperationalError as e:
            self.log.error("Database connection error: %s", e)
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
                # skipcq: BAN-B608
                query = f'UPDATE tasks SET {set_clause} WHERE id = ?'
                values = list(validated_updates.values()) + [task_id]
                cursor.execute(query, values)
                if cursor.rowcount == 0:
                    raise DatabaseError(f"No task found with ID {task_id}", "TASK_NOT_FOUND")
                conn.commit()
        except sqlite3.OperationalError as e:
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            self.log.error("Error updating task: %s", e)
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
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def get_task(self, task_id):
        """Retrieve a task by ID."""
        op_id = self.generate_operation_id()
        self._log_operation("get_task", {"task_id": task_id}, op_id)

        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                task = cursor.fetchone()

                if task is None:
                    self.log.warning("Task not found [OperationID: %s, TaskID: %d]",
                                     op_id, task_id)
                    raise DatabaseError("Task not found", "TASK_NOT_FOUND")

                self.log.info("Task retrieved successfully [OperationID: %s, TaskID: %d]",
                              op_id, task_id)
                task_list = list(task)
                task_list[2] = bool(task_list[2])
                return tuple(task_list)
        except sqlite3.OperationalError as e:
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except Exception as e:
            self.log.error("Failed to get task [OperationID: %s] - Error: %s",
                           op_id, str(e), exc_info=True)
            raise

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
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e

    def add_label(self, name, color=None):  # skipcq: PYL-R1710
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
                    self.log.info("Label operation successful. Label ID: %d", label_id)
                    return label_id

        except sqlite3.OperationalError as e:
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
        except sqlite3.Error as e:
            self.log.error("Error adding label: %s", e)
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
            self.log.error("Database connection error: %s", e)
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
            self.log.error("Database connection error: %s", e)
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
            self.log.error("Database connection error: %s", e)
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
            self.log.error("Database connection error: %s", e)
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
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database",
                                "DB_CONN_ERROR") from e

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

                try:
                    cursor.execute(query, (task_id, label_id))
                except sqlite3.IntegrityError as err:
                    raise DatabaseError("Task-label link already exists",
                                        "LINK_EXISTS") from err

        except sqlite3.OperationalError as e:
            self.log.error("Database connection error: %s", e)
            raise DatabaseError("An error occurred while connecting to the database", "DB_CONN_ERROR") from e
