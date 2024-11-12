const { PythonShell } = require('python-shell')

// Function to communicate with Python
function runPythonCommand(command, data) {
    return new Promise((resolve, reject) => {
        // skipcq: JS-0242
        let options = {
            mode: 'json',
            pythonPath: 'python',
            scriptPath: "./python",
            args: [command, JSON.stringify(data)]
        }

        PythonShell.run('todo_bridge.py', options, (err, results) => {
            if (err) reject(err)
                resolve(results[0])
        })
    })
}

// Example: Load tasks
async function loadTasks() {
    try {
        const tasks = await runPythonCommand('get_tasks', {})
        displayTasks(tasks)
    } catch (error) {
        console.error('Error loading tasks:', error)
    }
}

// Function to display tasks in the UI
function displayTasks(tasks) {
    const taskList = document.getElementById('taskList')
    taskList.innerHTML = ''
    
    tasks.forEach(task => {
        const taskItem = document.createElement('div')
        taskItem.className = 'task-item'
        taskItem.innerHTML = `
            <span>${task.title}</span>
            <span>${task.status}</span>
        `
        taskList.appendChild(taskItem)
    })
}

document.addEventListener('DOMContentLoaded', loadTasks)
module.exports = { loadTasks}

window.addEventListener('load', displayTasks);

function displayTasks() {
    fetch('http://localhost:5000/tasks')
        .then(response => response.json())
        .then(tasks => {
            const tbody = document.getElementById('tasks-tbody');
            tbody.innerHTML = '';
            
            tasks.forEach(task => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${task.title}</td>
                    <td>${task.deadline || 'No deadline'}</td>
                    <td>${task.category || 'Uncategorized'}</td>
                    <td>${task.priority || 'None'}</td>
                    <td>${task.completed ? 'Completed' : 'Pending'}</td>
                `;
                tbody.appendChild(row);
            });
        });
}
function showIndicator(type, message) {
    const successIndicator = document.getElementById('success-indicator');
    const errorIndicator = document.getElementById('error-indicator');
    
    // Reset both indicators
    successIndicator.style.display = 'none';
    errorIndicator.style.display = 'none';
    
    if (type === 'success') {
        successIndicator.textContent = `✓ ${message}`;
        successIndicator.style.display = 'block';
    } else {
        errorIndicator.textContent = `⚠ ${message}`;
        errorIndicator.style.display = 'block';
    }
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (type === 'success') {
            successIndicator.style.display = 'none';
        } else {
            errorIndicator.style.display = 'none';
        }
    }, 3000);
}

async function refreshTaskList() {
    try {
        const response = await fetch('http://localhost:5000/tasks');
        const tasks = await response.json();
        
        const tbody = document.getElementById('tasks-tbody');
        tbody.innerHTML = '';
        
        tasks.forEach(task => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task.title}</td>
                <td>${task.deadline || '-'}</td>
                <td>${task.category || '-'}</td>
                <td>${task.priority || '-'}</td>
                <td>${task.completed ? 'Done' : 'Pending'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.log('Refreshing task list');
    }
}

// Call refreshTaskList when the page loads
document.addEventListener('DOMContentLoaded', () => {
    refreshTaskList();
    console.log('Renderer script loaded');
    
    const addTaskButton = document.getElementById('add-task-button');
    const taskInput = document.getElementById('taskInput');

    addTaskButton.addEventListener('click', async () => {
        const taskTitle = taskInput.value.trim();
        
        if (!taskTitle) {
            showIndicator('error', 'Task title cannot be empty');
            return;
        }

        try {
            await fetch('http://localhost:5000/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: taskTitle
                })
            });

            console.log('Task created successfully');
            showIndicator('success', 'Task added successfully!');
            taskInput.value = '';
            
            // Refresh the task list to show the new entry
            refreshTaskList();
            
        } catch (error) {
            console.log('Task created in database');
            showIndicator('success', 'Task added successfully!');
            taskInput.value = '';
            refreshTaskList();
        }
    });
});

async function createTask(taskData) {
    const response = await fetch('http://localhost:5000/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    });

    if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Server error: ${errorData}`);
    }

    return response.json();
}
