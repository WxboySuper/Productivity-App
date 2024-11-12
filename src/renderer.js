// Add this at the top of the file to test DOM loading
console.log('Renderer script loaded');

document.addEventListener('DOMContentLoaded', () => {
    const addButton = document.getElementById('add-task-button');
    
    if (addButton) {
        addButton.addEventListener('click', () => {
            console.log('Button clicked!');
        });
    } else {
        console.log('Button element not found - check HTML IDs');
    }
});

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

document.getElementById('add-task-button').addEventListener('click', () => {
    const taskData = {
        title: document.getElementById('task-title').value,
        deadline: document.getElementById('task-deadline').value,
        category: document.getElementById('task-category').value,
        priority: document.getElementById('task-priority').value
    };

    fetch('http://localhost:5000/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        console.log('Response status:', response.status);  // Debug log
        return response.json();
    })
    .then(data => {
        console.log('Task created:', data);  // Debug log
        displayTasks();
    })
    .catch(error => {
        console.error('Error creating task:', error);  // Debug log
    });
});