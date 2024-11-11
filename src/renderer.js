const { PythonShell } = require('python-shell')

// Function to communicate with Python
function runPythonCommand(command, data) {
    return new Promise((resolve, reject) => {
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

// Add more UI interaction fucntions here