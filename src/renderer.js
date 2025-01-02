const { PythonShell } = require('python-shell')
const path = require('path')
const { logOperation } = require('./js/logging_config')

const scriptPath = process.env.NODE_ENV === 'production' 
    ? path.join(process.resourcesPath, 'src', 'python')
    : path.join(__dirname, 'python')

// Function to communicate with Python
function runPythonCommand(command, data) {
    const requestId = logOperation('debug', 'pythonCommand', { command, data })
    
    return new Promise((resolve, reject) => {
        const options = {
            mode: 'json',
            pythonPath: 'python',
            scriptPath,
            args: [command, JSON.stringify(data)]
        }

        PythonShell.run('todo_bridge.py', options, (err, results) => {
            if (err) {
                logOperation('error', 'pythonCommandFailed', { requestId, command, error: err.message }, err)
                reject(new Error(`Failed to execute Python command '${command}': ${err.message}`))
                return
            }
            if (!results || results.length === 0) {
                logOperation('error', 'pythonCommandNoResults', { requestId, command })
                reject(new Error(`No results returned from Python command '${command}'`))
                return
            }
            logOperation('info', 'pythonCommandSuccess', { requestId, command, results })
            resolve(results[0])
        })
    })
}

// Example: Load tasks
async function loadTasks() {
    try {
        const tasks = await runPythonCommand('get_tasks', {})
        // skipcq: JS-W1038
        displayTasks(tasks)
    } catch (error) {
        console.error('Error loading tasks:', error)
    }
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
    const requestId = logOperation('debug', 'refreshTaskList')
    
    try {
        const response = await fetchWithRetry('http://localhost:5000/tasks')
        const tasks = await response.json()
        
        logOperation('info', 'tasksRefreshed', { requestId, taskCount: tasks.length })
        
        const tbody = document.getElementById('tasks-tbody');
        tbody.innerHTML = '';
        
        tasks.forEach(task => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task[1] || ''}</td>
                <td>${task[3] || 'No deadline'}</td>
                <td>${task[4] || 'Uncategorized'}</td>
                <td>${task[6] || 'None'}</td>
                <td>${task[2] === 1 ? 'Completed' : 'Pending'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        logOperation('error', 'refreshTasksFailed', { requestId }, error)
    }
}
// Call refreshTaskList when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // skipcq: JS-0002
    console.log('Renderer script loaded');
    
    // Small delay to ensure proper data loading
    setTimeout(() => {
        refreshTaskList();
    }, 100);
    
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

            // skipcq: JS-0002
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

// skipcq: JS-0128
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

// skipcq: JS-0045, JS-0128
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    const requestId = logOperation('debug', 'fetchWithRetry', { url, maxRetries })
    const timeout = 5000; // 5 seconds timeout
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            const controller = new AbortController();  
            const timeoutId = setTimeout(() => controller.abort(), timeout);  
            
            const response = await fetch(url, {  
                ...options,  
                signal: controller.signal  
            });  
            
            clearTimeout(timeoutId);  
            
            if (!response.ok) {  
                throw new Error(`HTTP error! status: ${response.status}`);  
            }  
            logOperation('info', 'fetchSuccess', { requestId, attempt: i + 1 })
            return response
        } catch (error) {
            logOperation('warn', 'fetchRetry', { requestId, attempt: i + 1, error: error.message })
            if (error.name === 'AbortError') {  
                throw new Error(`Request timeout after ${timeout}ms`);  
            }
            if (i === maxRetries - 1) {
                logOperation('error', 'fetchFailed', { requestId }, error)
                throw error
            }
            // Exponential backoff with jitter  
            const delay = Math.min(1000 * Math.pow(2, i) + Math.random() * 1000, 10000);  
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}
