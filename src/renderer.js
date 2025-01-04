// Remove require statements
// const { logOperation } = require('./js/logging_config');
// const fs = require('fs');
// const path = require('path');
// const { ipcRenderer } = require('electron');

// Use exposed APIs instead
const logger = window.electronLogger;

async function fetchTasks() {
    try {
        const response = await fetch('http://localhost:5000/tasks');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        logOperation('error', 'fetchTasksFailed', {}, error);
        showIndicator('error', `Failed to load tasks: ${error.message}`);
        return [];
    }
}

async function addTask(taskData) {
    try {
        const response = await fetch('http://localhost:5000/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        logger.error({
            requestId: generateRequestId(),
            operation: 'addTaskFailed',
            timestamp: new Date().toISOString(),
            taskData,
            error: {
                message: error.message,
                stack: error.stack
            }
        });
        throw error;
    }
}

function displayTasks(tasks) {
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
}

/**
 * Shows a temporary status indicator
 * @function showIndicator
 */
function showIndicator(type, message) {
    const successIndicator = document.getElementById('success-indicator');
    const errorIndicator = document.getElementById('error-indicator');

    successIndicator.style.display = 'none';
    errorIndicator.style.display = 'none';

    if (type === 'success') {
        successIndicator.textContent = `✓ ${message}`;
        successIndicator.style.display = 'block';
    } else {
        errorIndicator.textContent = `⚠ ${message}`;
        errorIndicator.style.display = 'block';
    }
    
    setTimeout(() => {
        if (type === 'success') {
            successIndicator.style.display = 'none';
        } else {
            errorIndicator.style.display = 'none';
        }
    }, 3000);
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    // Use electronLogger.logOperation instead of logOperation directly
    window.electronLogger.logOperation('info', 'appInitialized');
    
    try {
        const tasks = await fetchTasks();
        displayTasks(tasks);
    } catch (error) {
        showIndicator('error', `Failed to load tasks: ${error.message}`);
    }
    
    const addTaskButton = document.getElementById('add-task-button');
    const taskInput = document.getElementById('taskInput');

    addTaskButton.addEventListener('click', async () => {
        const taskTitle = taskInput.value.trim();
        
        if (!taskTitle) {
            showIndicator('error', 'Task title cannot be empty');
            return;
        }

        try {
            await addTask({ title: taskTitle });
            const tasks = await fetchTasks();
            displayTasks(tasks);
            showIndicator('success', 'Task added successfully!');
            taskInput.value = '';
        } catch (error) {
            showIndicator('error', `Failed to add task: ${error.message}`);
        }
    });
});
