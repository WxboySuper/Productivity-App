import customtkinter as ctk
from datetime import datetime
from tkcalendar import Calendar
from database import TodoDatabase


class TodoList:
    def __init__(self):
        self.db = TodoDatabase()
        self.tasks = []

    def refresh_tasks(self):
        self.tasks = self.db.get_all_tasks()

    def add_task(self, task, deadline=None, category=None, notes=None, priority=None):
        task_id = self.db.add_task(task, deadline, category, notes, priority)
        self.refresh_tasks()
        print(f"Task '{task}' added successfully!")
        return task_id

    def mark_completed(self, task_index):
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            self.db.mark_completed(task_id)
            self.refresh_tasks()
            print("Task marked as completed!")
        else:
            print("Invalid task index!")

    def update_task(self, task_index, **updates):
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            self.db.update_task(task_id, **updates)
            self.refresh_tasks()
            print("Task updated successfully!")
        else:
            print("Invalid task index!")

    def delete_task(self, task_index):
        if 0 <= task_index < len(self.tasks):
            task_id = self.tasks[task_index][0]
            task = self.db.get_task(task_id)
            self.db.delete_task(task_id)
            self.refresh_tasks()
            print(f"Task '{task[1]}' deleted successfully!")
        else:
            print("Invalid task index!")


class TodoListGUI:
    def __init__(self):
        self.todo = TodoList()
        self.selected_task_index = None

        self.window = ctk.CTk()
        self.window.title("Todo List Application")
        self.window.geometry("800x600")

        self.labels_list = None
        self.detail_panel = None
        self.notes_area = None
        self.detail_title = None
        self.category_var = None
        self.category_menu = None
        self.priority_var = None
        self.priority_menu = None
        self.deadline_button = None
        self.save_button = None
        self.labels_frame = None
        self.label_entry = None
        self.add_label_button = None

        self.setup_main_layout()
        self.create_context_menu()
        self.bind_events()

        # Load existing tasks after GUI is ready
        self.todo.refresh_tasks()
        self.refresh_task_list()

    def setup_main_layout(self):
        self.list_panel = ctk.CTkFrame(self.window)
        self.list_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.quick_add_frame = ctk.CTkFrame(self.list_panel)
        self.quick_add_frame.pack(fill="x", padx=5, pady=5)

        self.task_entry = ctk.CTkEntry(self.quick_add_frame, placeholder_text="Quick add task...")
        self.task_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.add_button = ctk.CTkButton(self.quick_add_frame, text="+", width=30, command=self.quick_add_task)
        self.add_button.pack(side="right", padx=5)

        self.task_listbox = ctk.CTkTextbox(self.list_panel)
        self.task_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.setup_detail_panel()

    def setup_detail_panel(self):
        self.detail_panel = ctk.CTkFrame(self.window, width=300)
        self.detail_panel.pack(side="right", fill="both", padx=10, pady=10, expand=False)

        ctk.CTkLabel(self.detail_panel, text="Task Details").pack(pady=5)

        self.detail_title = ctk.CTkEntry(self.detail_panel, placeholder_text="Task title")
        self.detail_title.pack(fill="x", padx=10, pady=5)

        categories = ["Work", "Personal"]
        self.category_var = ctk.StringVar(value="Category")
        self.category_menu = ctk.CTkOptionMenu(
            self.detail_panel,
            values=categories,
            variable=self.category_var
        )
        self.category_menu.pack(fill="x", padx=10, pady=5)

        priorities = ["ASAP", "1", "2", "3", "4"]
        self.priority_var = ctk.StringVar(value="Priority")
        self.priority_menu = ctk.CTkOptionMenu(
            self.detail_panel,
            values=priorities,
            variable=self.priority_var
        )
        self.priority_menu.pack(fill="x", padx=10, pady=5)
        self.deadline_button = ctk.CTkButton(
            self.detail_panel,
            text="Set Deadline",
            command=self.show_calendar
        )
        self.deadline_button.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.detail_panel, text="Notes").pack(pady=5)
        self.notes_area = ctk.CTkTextbox(self.detail_panel, height=100)
        self.notes_area.pack(fill="x", padx=10, pady=5)

        self.save_button = ctk.CTkButton(
            self.detail_panel,
            text="Save Changes",
            command=self.save_task_details
        )
        self.save_button.pack(fill="x", padx=10, pady=5)

        self.labels_frame = ctk.CTkFrame(self.detail_panel)
        self.labels_frame.pack(fill="x", padx=10, pady=5)

        self.label_entry = ctk.CTkEntry(self.labels_frame, placeholder_text="New label...")
        self.label_entry.pack(side="left", fill="x", expand=True)

        self.add_label_button = ctk.CTkButton(
            self.labels_frame,
            text="+",
            width=30,
            command=self.create_label
        )
        self.add_label_button.pack(side="right")

        self.labels_list = ctk.CTkTextbox(self.detail_panel, height=100)
        self.labels_list.pack(fill="x", padx=10, pady=5)

    def create_label(self):
        label_name = self.label_entry.get()
        if label_name:
            label_id = self.todo.db.add_label(label_name)
            if self.selected_task_index is not None:
                task_id = self.todo.tasks[self.selected_task_index][0]
                self.todo.db.link_task_label(task_id, label_id)
            self.label_entry.delete(0, "end")
            self.refresh_labels()

    def refresh_labels(self):
        self.labels_list.delete("1.0", "end")
        if self.selected_task_index is not None:
            task_id = self.todo.tasks[self.selected_task_index][0]
            labels = self.todo.db.get_task_labels(task_id)
            for label in labels:
                self.labels_list.insert("end", f"#{label[1]} ")

    def create_context_menu(self):
        self.context_menu = ctk.CTkFrame(self.window)

        def create_command(cmd):
            def wrapped_command():
                cmd()
                self.context_menu.place_forget()  # Hide menu after action
            return wrapped_command

        actions = [
            ("Complete", self.mark_completed),
            ("Delete", self.delete_task)
        ]

        for text, command in actions:
            btn = ctk.CTkButton(
                self.context_menu,
                text=text,
                command=create_command(command)
            )
            btn.pack(pady=2, padx=2)

    def bind_events(self):
        self.task_listbox.bind("<Button-3>", self.show_context_menu)
        self.task_listbox.bind("<Button-1>", self.handle_task_selection)

    def show_context_menu(self, event):
        # Get task index from click position
        index = int(self.task_listbox.index(f"@{event.x},{event.y}").split('.')[0]) - 1
        if 0 <= index < len(self.todo.tasks):
            self.selected_task_index = index
            # Position menu at cursor
            x = self.window.winfo_pointerx() - self.window.winfo_rootx()
            y = self.window.winfo_pointery() - self.window.winfo_rooty()
            self.context_menu.place(x=x, y=y)

    def handle_task_selection(self, event):
        self.context_menu.place_forget()
        index = int(self.task_listbox.index(f"@{event.x},{event.y}").split('.')[0]) - 1
        if 0 <= index < len(self.todo.tasks):
            self.selected_task_index = index
            self.load_task_details(index)

    def load_task_details(self, index):
        task = self.todo.tasks[index]
        self.detail_title.delete(0, "end")
        self.detail_title.insert(0, task[1])  # task title
        self.category_var.set(task[4] or "Category")  # category
        self.notes_area.delete("1.0", "end")
        if task[5]:  # notes
            self.notes_area.insert("1.0", task[5])

    def save_task_details(self):
        if self.selected_task_index is not None:
            updates = {
                "title": self.detail_title.get(),
                "category": self.category_var.get(),
                "notes": self.notes_area.get("1.0", "end-1c")
            }
            self.todo.update_task(self.selected_task_index, **updates)
            self.refresh_task_list()

    def quick_add_task(self):
        task = self.task_entry.get()
        if task:
            priority = self.priority_var.get() if self.priority_var.get() != "Priority" else None
            category = self.category_var.get() if self.category_var.get() != "Category" else None
            self.todo.add_task(
                task,
                priority=priority,
                category=category
            )
            self.task_entry.delete(0, "end")
            self.refresh_task_list()

    def show_calendar(self):
        calendar_window = ctk.CTkToplevel(self.window)
        calendar_window.title("Select Deadline")

        cal = Calendar(calendar_window, selectmode='day', mindate=datetime.now())
        cal.pack(padx=10, pady=10)

        def set_deadline():
            if self.selected_task_index is not None:
                deadline = cal.get_date()
                self.todo.update_task(self.selected_task_index, deadline=deadline)
                self.refresh_task_list()
            calendar_window.destroy()

        confirm_button = ctk.CTkButton(
            calendar_window,
            text="Confirm",
            command=set_deadline
        )
        confirm_button.pack(pady=5)

    def mark_completed(self):
        if self.selected_task_index is not None:
            self.todo.mark_completed(self.selected_task_index)
            self.refresh_task_list()

    def delete_task(self):
        if self.selected_task_index is not None:
            self.todo.delete_task(self.selected_task_index)
            self.selected_task_index = None
            self.refresh_task_list()

    def refresh_task_list(self):
        self.task_listbox.delete("1.0", "end")
        for i, task in enumerate(self.todo.tasks):
            status = "✓" if task[2] else " "
            priority = f"[{task[6]}]" if task[6] else ""
            category = f"[{task[4]}]" if task[4] else ""
            deadline = f" (Due: {task[3]})" if task[3] else ""
            self.task_listbox.insert("end", f"{i}. [{status}] {priority} {task[1]} {category}{deadline}\n")

    def run(self):
        self.window.mainloop()


def main():
    app = TodoListGUI()
    app.run()


if __name__ == "__main__":
    main()
