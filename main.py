import customtkinter as ctk
from datetime import datetime
from tkcalendar import Calendar
from database import TodoDatabase


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

    def __init__(self):
        """
        Initializes the TodoList class with a TodoDatabase instance and an empty list of tasks.
        """    
        self.db = TodoDatabase()
        self.tasks = []

    def refresh_tasks(self):
        """
        Refreshes the list of tasks by retrieving all tasks from the database and updating the `tasks` attribute.
        """        
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
        print(f"Task '{task}' added successfully!")
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
            print("Task marked as completed!")
        else:
            print("Invalid task index!")

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
            print("Invalid task index!")

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
            print("Invalid task index!")


class TodoListGUI:
    """
    The `TodoListGUI` class represents the graphical user interface (GUI) for a todo list application.
    
    The class sets up the main window, creates the layout with a task list panel and a task detail panel,
    and provides methods to manage tasks, including adding, updating, marking as completed, and deleting tasks.
    It also handles task selection, context menus, and task labeling.
    
    The `run()` method starts the main event loop and displays the GUI.
    """

    def __init__(self):
        """
        The `__init__` method initializes the `TodoListGUI` class,
        which represents the graphical user interface (GUI) for a todo list application.
        
        It sets up the main window, creates the layout with a task list panel and a task detail panel,
        and provides methods to manage tasks, including adding, updating, marking as completed, and deleting tasks. It also handles task selection, context menus, and task labeling.
        
        The `run()` method starts the main event loop and displays the GUI.
        """
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
        """
        Sets up the main layout of the TodoListGUI, including the task list panel and the task detail panel.
        
        The `setup_main_layout` method creates the main layout of the TodoListGUI,
        which consists of a task list panel on the left and a task detail panel on the right.
        
        The task list panel includes a quick add frame with an entry field and a button to quickly add new tasks,
        as well as a listbox to display the list of tasks.
        
        The task detail panel is set up by calling the `setup_detail_panel` method.
        """
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
        """
        Sets up the task detail panel, which includes the following components:
        - Task title entry field
        - Category dropdown menu
        - Priority dropdown menu
        - Deadline button
        - Notes text area
        - Labels frame with an entry field and a button to add new labels
        - Labels list to display the labels associated with the selected task
        
        The `setup_detail_panel` method is responsible for creating and configuring the task detail panel,
        which is displayed on the right side of the TodoListGUI.
        """
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
        """
        Creates a new label and associates it with the currently selected task.
        
        If a label name is provided in the label entry field, a new label is added to the database and linked to the currently selected task.
        The label entry field is then cleared, and the labels list is refreshed to display the updated labels for the selected task.
        """
        label_name = self.label_entry.get()
        if label_name:
            label_id = self.todo.db.add_label(label_name)
            if self.selected_task_index is not None:
                task_id = self.todo.tasks[self.selected_task_index][0]
                self.todo.db.link_task_label(task_id, label_id)
            self.label_entry.delete(0, "end")
            self.refresh_labels()

    def refresh_labels(self):
        """
        Refreshes the labels list for the currently selected task.
        
        This method retrieves the labels associated with the currently selected task from the database,
        and displays them in the labels list widget. If no task is currently selected, the labels list is cleared.
        """
        self.labels_list.delete("1.0", "end")
        if self.selected_task_index is not None:
            task_id = self.todo.tasks[self.selected_task_index][0]
            labels = self.todo.db.get_task_labels(task_id)
            for label in labels:
                self.labels_list.insert("end", f"#{label[1]} ")

    def create_context_menu(self):
        """
        Creates a context menu for the task list, with options to mark a task as completed or delete a task.
        
        The context menu is a `CTkFrame` widget that contains two buttons: "Complete" and "Delete".
        When either button is clicked, the corresponding action function is called, and the context menu is hidden.
        
        The `create_command` function is used to wrap the action functions, so that the context menu is hidden after the action is performed.
        """
        self.context_menu = ctk.CTkFrame(self.window)

        def create_command(cmd):
            """
            Wraps a command function with additional logic to hide the context menu after the command is executed.
            
            This function is used to create a new command function that, when called,
            will execute the original command function and then hide the context menu.
            This is useful for context menu actions, where the menu should be hidden after the user selects an option.
            
            Args:
                cmd (callable): The original command function to be wrapped.
            
            Returns:
                callable: The new wrapped command function.
            """
            def wrapped_command():
                """
                Wraps a command function with additional logic to hide the context menu after the command is executed.
                
                This function is used to create a new command function that, when called,
                will execute the original command function and then hide the context menu.
                This is useful for context menu actions, where the menu should be hidden after the user selects an option.
                
                Args:
                    cmd (callable): The original command function to be wrapped.
                
                Returns:
                    callable: The new wrapped command function.
                """
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
        """
        Binds event handlers to the task listbox widget.
        
        The `bind_events` method sets up two event handlers for the `task_listbox` widget:
        
        1. `show_context_menu`: Binds a right-click (Button-3) event to display a context menu for the selected task.
        2. `handle_task_selection`: Binds a left-click (Button-1) event to handle the selection of a task in the listbox.
        
        These event handlers allow the user to interact with the task list,
        such as accessing a context menu for tasks and selecting tasks to view their details.
        """
        self.task_listbox.bind("<Button-3>", self.show_context_menu)
        self.task_listbox.bind("<Button-1>", self.handle_task_selection)

    def show_context_menu(self, event):
        """
        Displays a context menu for the selected task in the task listbox.
        
        This method is responsible for handling the right-click (Button-3) event on the task listbox.
        It retrieves the index of the task under the cursor, sets the `selected_task_index` attribute,
        and positions the context menu at the cursor location.
        
        The context menu provides actions such as "Complete" and "Delete" that can be performed on the selected task.
        """
        # Get task index from click position
        index = int(self.task_listbox.index(f"@{event.x},{event.y}").split('.')[0]) - 1
        if 0 <= index < len(self.todo.tasks):
            self.selected_task_index = index
            # Position menu at cursor
            x = self.window.winfo_pointerx() - self.window.winfo_rootx()
            y = self.window.winfo_pointery() - self.window.winfo_rooty()
            self.context_menu.place(x=x, y=y)

    def handle_task_selection(self, event):
        """
        Handles the selection of a task in the task listbox.
        
        This method is responsible for processing the left-click (Button-1) event on the task listbox.
        It first hides the context menu,
        then retrieves the index of the task under the cursor and sets the `selected_task_index` attribute.
        Finally, it calls the `load_task_details` method to display the details of the selected task.
        """
        self.context_menu.place_forget()
        index = int(self.task_listbox.index(f"@{event.x},{event.y}").split('.')[0]) - 1
        if 0 <= index < len(self.todo.tasks):
            self.selected_task_index = index
            self.load_task_details(index)

    def load_task_details(self, index):
        """
        Loads the details of the selected task and populates the corresponding UI elements.
        
        This method is responsible for displaying the details of the task selected in the task listbox.
        It retrieves the task data from the `self.todo.tasks` list using the provided `index` parameter,
        and then updates the UI elements such as the detail title, category, and notes area to reflect the task details.
        """
        task = self.todo.tasks[index]
        self.detail_title.delete(0, "end")
        self.detail_title.insert(0, task[1])  # task title
        self.category_var.set(task[4] or "Category")  # category
        self.notes_area.delete("1.0", "end")
        if task[5]:  # notes
            self.notes_area.insert("1.0", task[5])

    def save_task_details(self):
        """
        Updates the details of the currently selected task in the task list.
        
        This method is responsible for handling the saving of changes made to the details of the currently selected task.
        It retrieves the updated title, category, and notes from the corresponding UI elements,
        and then calls the `update_task` method of the `self.todo` object to update the task details.
        Finally, it refreshes the task list to reflect the changes.
        """
        if self.selected_task_index is not None:
            updates = {
                "title": self.detail_title.get(),
                "category": self.category_var.get(),
                "notes": self.notes_area.get("1.0", "end-1c")
            }
            self.todo.update_task(self.selected_task_index, **updates)
            self.refresh_task_list()

    def quick_add_task(self):
        """
        Adds a new task to the todo list and refreshes the task list display.
        
        This method is responsible for handling the addition of a new task to the todo list.
        It retrieves the task title from the task entry field,
        and optionally the priority and category from the corresponding dropdown menus.
        It then calls the `add_task` method of the `self.todo` object to add the new task,
        and finally refreshes the task list display by calling the `refresh_task_list` method.
        """
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
        """
        Displays a calendar window to allow the user to select a deadline for the currently selected task.
        
        This method creates a new `CTkToplevel` window and adds a `Calendar` widget to it.
        When the user selects a date, the `set_deadline` function is called,
        which updates the deadline for the currently selected task in the `self.todo` object and refreshes the task list display.
        """
        calendar_window = ctk.CTkToplevel(self.window)
        calendar_window.title("Select Deadline")

        cal = Calendar(calendar_window, selectmode='day', mindate=datetime.now())
        cal.pack(padx=10, pady=10)

        def set_deadline():
            """
            Sets the deadline for the currently selected task in the todo list.
            
            This function is called when the user selects a date in the calendar window displayed by the `show_calendar` method.
            It retrieves the selected date from the calendar,
            updates the deadline for the currently selected task in the `self.todo` object,
            and then refreshes the task list display to reflect the change.
            
            If no task is currently selected, this function does nothing.
            """
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
        """
        Marks the currently selected task as completed and refreshes the task list display.
        
        This method is responsible for updating the completion status of the currently selected task in the todo list.
        It retrieves the index of the selected task from the `self.selected_task_index` attribute,
        and then calls the `mark_completed` method of the `self.todo` object to update the task's completion status.
        Finally, it calls the `refresh_task_list` method to update the task list display to reflect the change.
        
        If no task is currently selected, this method does nothing.
        """
        if self.selected_task_index is not None:
            self.todo.mark_completed(self.selected_task_index)
            self.refresh_task_list()

    def delete_task(self):
        """
        Deletes the currently selected task from the todo list and refreshes the task list display.
        
        This method is responsible for removing the currently selected task from the todo list.
        It retrieves the index of the selected task from the `self.selected_task_index` attribute,
        and then calls the `delete_task` method of the `self.todo` object to remove the task.
        Finally, it sets the `self.selected_task_index` attribute to `None` and
        calls the `refresh_task_list` method to update the task list display to reflect the change.
        
        If no task is currently selected, this method does nothing.
        """
        if self.selected_task_index is not None:
            self.todo.delete_task(self.selected_task_index)
            self.selected_task_index = None
            self.refresh_task_list()

    def refresh_task_list(self):
        """
        Refreshes the task list display in the GUI.
        
        This method is responsible for updating the task list display to reflect the current state of the todo list.
        It first clears the existing task list,
        then iterates through the tasks in the `self.todo.tasks` list and adds each task to the list display.
        The task display includes the task index, completion status, priority, title, category, and deadline (if set).
        
        If no tasks are currently in the todo list, this method will clear the task list display.
        """
        self.task_listbox.delete("1.0", "end")
        for i, task in enumerate(self.todo.tasks):
            status = "✓" if task[2] else " "
            priority = f"[{task[6]}]" if task[6] else ""
            category = f"[{task[4]}]" if task[4] else ""
            deadline = f" (Due: {task[3]})" if task[3] else ""
            self.task_listbox.insert("end", f"{i}. [{status}] {priority} {task[1]} {category}{deadline}\n")

    def run(self):
        """
        Runs the main event loop of the application window.
        
        This method is responsible for starting the main event loop of the application window,
        which will keep the window open and responsive to user interactions until the window is closed.
        It should be called after all the GUI components have been set up and configured.
        """
        self.window.mainloop()


def main():
    """
    The main entry point of the application.
    This function creates an instance of the TodoListGUI class and runs the main event loop, starting the application.
    """
    app = TodoListGUI()
    app.run()


if __name__ == "__main__":
    main()
