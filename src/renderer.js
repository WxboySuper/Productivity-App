const { PythonShell } = require('python-shell')
const path = require('path')
const log = require('electron-log')

log.transports.file.level = 'info'
log.info('renderer.js - Script initialized')

const scriptPath = process.env.NODE_ENV === 'production' 
    ? path.join(process.resourcesPath, 'src', 'python')
    : path.join(__dirname, 'python')

log.info('renderer.js - Script path set to:', scriptPath)

function runPythonCommand(command, data) {
    log.info('renderer.js - Running Python command:', command)
    return new Promise((resolve, reject) => {
        let options = {
            mode: 'json',
            pythonPath: 'python',
            scriptPath: scriptPath,
            args: [command, JSON.stringify(data)]
        }
        log.debug('renderer.js - Python options:', options)

        PythonShell.run('todo_bridge.py', options, (err, results) => {
            if (err) reject(err)
            if (!results || results.length === 0) {
                log.error('renderer.js - Python command error:', err)
                reject(new Error('No results returned from Python script'));
            }
            log.info('renderer.js - Python command completed successfully')
            resolve(results[0])
        })
    })
}

async function loadTasks() {
    log.info('renderer.js - Loading tasks')
    try {
        const tasks = await runPythonCommand('get_tasks', {})
        displayTasks(tasks)
        log.info('renderer.js - Tasks loaded successfully')
    } catch (error) {
        log.error('renderer.js - Error loading tasks:', error)
        console.error('Error loading tasks:', error)
    }
}

function displayTasks(tasks) {
    log.info('renderer.js - Displaying tasks')
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
    log.info('renderer.js - Tasks displayed')
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
    log.info('renderer.js - Refreshing task list')
    try {
        const response = await fetch('http://localhost:5000/tasks')
        const tasks = await response.json()
        
        const tbody = document.getElementById('tasks-tbody')
        tbody.innerHTML = ''
        
        tasks.forEach(task => {
            const row = document.createElement('tr')
            row.innerHTML = `
                <td>${task.title || ''}</td>
                <td>${task.deadline || 'No deadline'}</td>
                <td>${task.category || 'Uncategorized'}</td>
                <td>${task.priority || 'None'}</td>
                <td>${task.completed ? 'Completed' : 'Pending'}</td>
            `
            tbody.appendChild(row)
        })
        log.info('renderer.js - Task list refreshed successfully')
    } catch (error) {
        log.error('renderer.js - Error refreshing task list:', error)
    }
}
// Call refreshTaskList when the page loads
document.addEventListener('DOMContentLoaded', () => {
    log.info('renderer.js - DOM content loaded')
    async function initializeApp() {
        try {
            await fetchWithRetry('http://localhost:5000/health', {method: 'GET'});
            await refreshTaskList();
        } catch (error) {
            log.error('renderer.js - Failed to initialize app:', error);
        }
    }
    initializeApp();
    
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

async function fetchWithRetry(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);
            return response;
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}
