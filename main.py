class TodoList:
    def __init__(self):
        """
        Initializes a new TodoList instance.
        
        The TodoList class is used to manage a list of tasks. This constructor initializes an empty list to store the tasks.
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
            print(f"Task marked as completed!")
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
            print(f"Task updated successfully!")
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
        
        If the list of tasks is empty, it prints a message indicating that there are no tasks.
        
        Otherwise, it prints the list of tasks, with each task's index, status (indicated by a checkmark if completed, or a space if not), and task text.
        """
                
        if not self.tasks:
            print("No tasks in the list!")
            return
        print("\nTodo List:")
        for i, task in enumerate(self.tasks):
            status = "✓" if task["completed"] else " "
            print(f"{i}. [{status}] {task['task']}")

def main():
    """
    This is the main entry point for the Todo List application. It provides a command-line interface for users to interact with the TodoList class, allowing them to add, mark as completed, update, delete, and display tasks.
    
    The main function runs in an infinite loop, presenting the user with a menu of options and handling the user's choices accordingly. It utilizes the methods of the TodoList class to manage the todo list.
    """
        
    todo = TodoList()
    while True:
        print("\n=== Todo List Application ===")
        print("1. Add Task")
        print("2. Mark Task as Completed")
        print("3. Update Task")
        print("4. Delete Task")
        print("5. Display Tasks")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ")

        if choice == "1":
            task = input("Enter task: ")
            todo.add_task(task)
        
        elif choice == "2":
            todo.display_tasks()
            task_index = int(input("Enter task number to mark as completed: "))
            todo.mark_completed(task_index)
        
        elif choice == "3":
            todo.display_tasks()
            task_index = int(input("Enter task number to update: "))
            new_task = input("Enter new task: ")
            todo.update_task(task_index, new_task)
        
        elif choice == "4":
            todo.display_tasks()
            task_index = int(input("Enter task number to delete: "))
            todo.delete_task(task_index)
        
        elif choice == "5":
            todo.display_tasks()
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()
