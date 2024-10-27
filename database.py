import sqlite3

class TodoDatabase:
    def __init__(self, db_file="todo.db"):
        self.db_file = db_file
        self.init_database()

    def __del__(self):
        try:
            self.conn.close()
        except:
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
        # Whitelist of allowed fields for updates
        valid_fields = {'title', 'completed', 'deadline', 'category', 'notes', 'priority'}
        # Filter updates to only include valid fields
        update_fields = {k: v for k, v in updates.items() if k in valid_fields}

        if not update_fields:
            return

        # Build the parameterized query
        placeholders = [f"{field} = ?" for field in update_fields]
        query = f"UPDATE tasks SET {', '.join(placeholders)} WHERE id = ?"

        # Create values tuple with only the values
        values = tuple(update_fields.values()) + (task_id,)

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
