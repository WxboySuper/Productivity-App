import customtkinter as ctk


class TodoList:
    """
    The TodoList class is used to manage a list of tasks.
    It provides methods to add, mark as completed, update, delete, and display tasks.

    The class has the following methods:

    add_task(task):
        Adds a new task to the TodoList.
        Args:
            task (str): The text of the new task to add.

    mark_completed(task_index):
        Marks the task at the specified index as completed.
        Args:
            task_index (int): The index of the task to mark as completed.
        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.

    update_task(task_index, new_task):
        Updates the task at the specified index with the new task text.
        Args:
            task_index (int): The index of the task to update.
            new_task (str): The new task text to set.
        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.

    delete_task(task_index):
        Deletes the task at the specified index from the TodoList.
        Args:
            task_index (int): The index of the task to delete.
        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.

    display_tasks():
        Displays the current list of tasks, including their status (completed or not).
        If the list of tasks is empty,
        it prints a message indicating that there are no tasks.
        Otherwise, it prints the list of tasks, with each task's index,
        status (indicated by a checkmark if completed, or a space if not),
        and task text.
    """

    def __init__(self):
        """
        Initializes a new TodoList instance.

        The TodoList class is used to manage a list of tasks.
        This constructor initializes an empty list to store the tasks.
        """
        self.tasks = []

    def add_task(self, task):
        """
        Adds a new task to the TodoList.

        Args:
            task (str): The text of the new task to add.

        Returns:
            None
        """
        self.tasks.append({"task": task, "completed": False})
        print(f"Task '{task}' added successfully!")

    def mark_completed(self, task_index):
        """
        Marks the task at the specified index as completed.

        Args:
            task_index (int): The index of the task to mark as completed.

        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]["completed"] = True
            print("Task marked as completed!")
        else:
            print("Invalid task index!")

    def update_task(self, task_index, new_task):
        """
        Updates the task at the specified index with the new task text.

        Args:
            task_index (int): The index of the task to update.
            new_task (str): The new task text to set.

        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index]["task"] = new_task
            print("Task updated successfully!")
        else:
            print("Invalid task index!")

    def delete_task(self, task_index):
        """
        Deletes the task at the specified index from the TodoList.

        Args:
            task_index (int): The index of the task to delete.

        Raises:
            IndexError: If the `task_index` is out of range of the `self.tasks` list.
        """
        if 0 <= task_index < len(self.tasks):
            removed_task = self.tasks.pop(task_index)
            print(f"Task '{removed_task['task']}' deleted successfully!")
        else:
            print("Invalid task index!")

    def display_tasks(self):
        """
        Displays the current list of tasks, including their status (completed or not).

        If the list of tasks is empty,
        it prints a message indicating that there are no tasks.

        Otherwise, it prints the list of tasks, with each task's index,
        status (indicated by a checkmark if completed, or a space if not),
        and task text.
        """
        if not self.tasks:
            print("No tasks in the list!")
            return
        print("\n=== Todo List ===")  # Updated header format
        for i, task in enumerate(self.tasks):
            status = "✓" if task["completed"] else " "
            print(f"{i}. [{status}] {task['task']}")


class TodoListGUI:
    """
    A graphical user interface for the TodoList application using customtkinter.
    
    This class creates a window with input fields, buttons, and a display area
    for managing tasks in a visual way. It wraps the TodoList class functionality
    in a user-friendly interface.

    Attributes:
        window (CTk): The main application window
        todo (TodoList): Instance of TodoList class to manage tasks
        task_entry (CTkEntry): Input field for new tasks
        task_listbox (CTkTextbox): Display area for all tasks
    """

    def __init__(self):
        """
        Initializes the GUI window and creates all necessary widgets.
        Sets up the layout with frames for input, task list, and action buttons.
        """
        self.todo = TodoList()
        
        # Configure the window
        self.window = ctk.CTk()
        self.window.title("Todo List Application")
        self.window.geometry("600x400")
        
        # Create frames
        self.input_frame = ctk.CTkFrame(self.window)
        self.input_frame.pack(pady=10, padx=10, fill="x")
        
        self.list_frame = ctk.CTkFrame(self.window)
        self.list_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Create input elements
        self.task_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter task...")
        self.task_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.add_button = ctk.CTkButton(self.input_frame, text="Add Task", command=self.add_task)
        self.add_button.pack(side="right", padx=5)
        
        # Create task list
        self.task_listbox = ctk.CTkTextbox(self.list_frame)
        self.task_listbox.pack(pady=5, padx=5, fill="both", expand=True)
        
        # Create action buttons
        self.button_frame = ctk.CTkFrame(self.window)
        self.button_frame.pack(pady=10, padx=10, fill="x")
        
        self.complete_button = ctk.CTkButton(self.button_frame, text="Mark Completed", command=self.mark_completed)
        self.complete_button.pack(side="left", padx=5)
        
        self.update_button = ctk.CTkButton(self.button_frame, text="Update Task", command=self.update_task)
        self.update_button.pack(side="left", padx=5)
        
        self.delete_button = ctk.CTkButton(self.button_frame, text="Delete Task", command=self.delete_task)
        self.delete_button.pack(side="left", padx=5)
        
        self.refresh_task_list()

    def add_task(self):
        """
        Handles the addition of a new task from the input field.
        Retrieves the text from task_entry, adds it to the todo list,
        clears the input field, and refreshes the display.
        """
        task = self.task_entry.get()
        if task:
            self.todo.add_task(task)
            self.task_entry.delete(0, "end")
            self.refresh_task_list()

    def mark_completed(self):
        """
        Marks the selected task as completed.
        Gets the currently selected task from the textbox,
        finds its index, and marks it as completed in the todo list.
        Refreshes the display to show the updated status.
        """
        try:
            selected_text = self.task_listbox.get("1.0", "end-1c")
            current_line = self.task_listbox.index("insert").split('.')[0]
            lines = selected_text.split('\n')
            if 0 <= int(current_line) - 1 < len(lines):
                self.todo.mark_completed(int(current_line) - 1)
            self.refresh_task_list()
        except Exception:
            pass

    def update_task(self):
        """
        Updates the selected task with new text.
        Opens a dialog for entering new task text,
        updates the selected task in the todo list,
        and refreshes the display.
        """
        try:
            selected_text = self.task_listbox.get("1.0", "end-1c")
            current_line = self.task_listbox.index("insert").split('.')[0]
            lines = selected_text.split('\n')
            if 0 <= int(current_line) - 1 < len(lines):
                dialog = ctk.CTkInputDialog(text="Enter new task:", title="Update Task")
                new_task = dialog.get_input()
                if new_task:
                    self.todo.update_task(int(current_line) - 1, new_task)
            self.refresh_task_list()
        except Exception:
            pass

    def delete_task(self):
        """
        Deletes the selected task from the todo list.
        Gets the currently selected task,
        removes it from the todo list,
        and refreshes the display.
        """
        try:
            selected_text = self.task_listbox.get("1.0", "end-1c")
            current_line = self.task_listbox.index("insert").split('.')[0]
            lines = selected_text.split('\n')
            if 0 <= int(current_line) - 1 < len(lines):
                self.todo.delete_task(int(current_line) - 1)
            self.refresh_task_list()
        except Exception:
            pass
    def refresh_task_list(self):
        """
        Updates the task display area with the current state of the todo list.
        Clears the current display and repopulates it with all tasks,
        showing their index, completion status, and text.
        """
        self.task_listbox.delete("1.0", "end")
        for i, task in enumerate(self.todo.tasks):
            status = "✓" if task["completed"] else " "
            self.task_listbox.insert("end", f"{i}. [{status}] {task['task']}\n")

    def run(self):
        """
        Starts the GUI application main loop.
        This method must be called to display the window and handle user interactions.
        """
        self.window.mainloop()


def main():
    """
    Creates and runs the TodoList GUI application.
    This is the entry point for the graphical version of the todo list application.
    """
    app = TodoListGUI()
    app.run()


if __name__ == "__main__":
    main()
