import sqlite3
from datetime import datetime

class TodoDatabase:
    def __init__(self, db_file="todo.db"):
        self.db_file = db_file
        self.init_database()

    def __del__(self):
        # Ensure connections are closed
        try:
            self.conn.close()
        except:
            pass

    def init_database(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
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

    def add_label(self, name, color="#1f538d"):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO labels (name, color) VALUES (?, ?)', (name, color))
            return cursor.lastrowid

    def delete_label(self, label_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM task_labels WHERE label_id = ?', (label_id,))
            cursor.execute('DELETE FROM labels WHERE id = ?', (label_id,))

    def get_all_labels(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM labels')
            return cursor.fetchall()

    def link_task_label(self, task_id, label_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO task_labels (task_id, label_id) VALUES (?, ?)', 
                          (task_id, label_id))

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
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tasks (title, deadline, category, notes, priority) VALUES (?, ?, ?, ?, ?)',
                (title, deadline, category, notes, priority)
            )
            conn.commit()
            return cursor.lastrowid

    def mark_completed(self, task_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tasks SET completed = TRUE WHERE id = ?',
                (task_id,)
            )

    def update_task(self, task_id, **updates):
        valid_fields = {'title', 'completed', 'deadline', 'category', 'notes', 'priority'}
        update_fields = {k: v for k, v in updates.items() if k in valid_fields}

        if not update_fields:
            return

        query = 'UPDATE tasks SET ' + ', '.join(f'{k} = ?' for k in update_fields)
        query += ' WHERE id = ?'

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (*update_fields.values(), task_id))

    def delete_task(self, task_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    def get_all_tasks(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
            return cursor.fetchall()

    def get_task(self, task_id):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            return cursor.fetchone()
