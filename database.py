import sqlite3


class TodoDatabase:
    def __init__(self, db_file="todo.db"):
        self.db_file = db_file
        self.init_database()

    def __del__(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def init_database(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            # These CREATE TABLE statements are safe as they don't use any user input
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    deadline TEXT,
                    category TEXT,
                    notes TEXT,
                    priority TEXT CHECK(priority IN ('ASAP', '1', '2', '3', '4')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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

    def update_task(self, task_id, **updates):
        # Define strict whitelist of allowed fields and their types
        ALLOWED_UPDATES = {
            'title': str,
            'completed': bool,
            'deadline': str,
            'category': str,
            'notes': str,
            'priority': str
        }

        # Validate priority values against allowed options
        VALID_PRIORITIES = {'ASAP', '1', '2', '3', '4'}

        # Filter and validate updates
        validated_updates = {}
        for field, value in updates.items():
            if field not in ALLOWED_UPDATES:
                continue

            # Type validation
            if not isinstance(value, ALLOWED_UPDATES[field]):
                continue

            # Additional validation for priority field
            if field == 'priority' and value not in VALID_PRIORITIES:
                continue

            validated_updates[field] = value

        if not validated_updates:
            return

        # Use static query structure with parameterized values
        # skipcq: BAN-B608
        query = '''UPDATE tasks SET ''' + ', '.join(f'{field} = ?' for field in ALLOWED_UPDATES if field in validated_updates) + ''' WHERE id = ?'''

        # Create values tuple with only the values, in the same order as the query
        values = tuple(validated_updates[field] for field in ALLOWED_UPDATES if field in validated_updates) + (task_id,)

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)

    def get_task_labels(self, task_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.* FROM labels l
                JOIN task_labels tl ON l.id = tl.label_id
                WHERE tl.task_id = ?
            ''', (task_id,))
            return cursor.fetchall()

    def add_task(self, title, deadline=None, category=None, notes=None, priority=None):
        query = '''INSERT INTO tasks (title, deadline, category, notes, priority)
                  VALUES (?, ?, ?, ?, ?)'''
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, deadline, category, notes, priority))
            return cursor.lastrowid

    def mark_completed(self, task_id):
        query = 'UPDATE tasks SET completed = TRUE WHERE id = ?'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))

    def delete_task(self, task_id):
        query = 'DELETE FROM tasks WHERE id = ?'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))

    def get_all_tasks(self):
        query = 'SELECT * FROM tasks ORDER BY created_at DESC'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def get_task(self, task_id):
        query = 'SELECT * FROM tasks WHERE id = ?'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id,))
            return cursor.fetchone()

    def add_label(self, name, color="#1f538d"):
        query = 'INSERT INTO labels (name, color) VALUES (?, ?)'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (name, color))
            return cursor.lastrowid

    def delete_label(self, label_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM task_labels WHERE label_id = ?', (label_id,))
            cursor.execute('DELETE FROM labels WHERE id = ?', (label_id,))

    def get_all_labels(self):
        query = 'SELECT * FROM labels'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def link_task_label(self, task_id, label_id):
        query = 'INSERT INTO task_labels (task_id, label_id) VALUES (?, ?)'
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (task_id, label_id))
