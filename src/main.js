const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

const log = require('electron-log')
log.transports.file.level = 'info';

const { PythonShell } = require('python-shell');
const pythonPath = 'python'

let serverProcess = null
let bridgeProcess = null

function startBackendProcesses() {
    const userDataPath = app.getPath('userData');
    log.info('main.js - User data path:', userDataPath);
    
    const dbPath = path.join(userDataPath, 'todo.db');
    log.info('main.js - Database path:', dbPath);
    
    const baseDir = app.isPackaged 
        ? path.join(process.resourcesPath, 'src', 'python')
        : path.join(__dirname, '../src/python');
    
    log.info('main.js - Base directory:', baseDir);
    log.info('main.js - Python executable:', pythonPath);
    
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')

    log.info('main.js - Python scripts directory:', baseDir)
    log.info('main.js - Server script path:', serverScript)

    serverProcess = spawn(pythonPath, [serverScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    }).on('error', (err) => {
        log.error('main.js - Failed to start server process:', err)
    })

    let serverReady = false
    let bridgeReady = false

    const PROCESS_READY_TIMEOUT = 30000; // 30 second timeout
    let readinessTimeout;
    function initializeReadinessCheck() {  
            readinessTimeout = setTimeout(() => {  
                if (!serverReady || !bridgeReady) {  
                    log.error('main.js - Timeout waiting for processes to become ready');  
                    app.quit();  
                }  
            }, PROCESS_READY_TIMEOUT);  
        }  

    serverProcess.stdout.on('data', (data) => {
        log.info(`main.js - Server output: ${data}`);
        if (data.toString().includes('Running on')) {
            log.info('main.js - Flask server started successfully')
            serverReady = true;
            checkAllProcessesReady()
        }
    })

    serverProcess.stderr.on('data', (data) => {
        log.error(`main.js - Server Error: ${data.toString()}`)
    })

    bridgeProcess = spawn(pythonPath, [bridgeScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    }).on('error', (err) => {
        log.error('main.js - Failed to start bridge process:', err)
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        log.info(`main.js - Bridge: ${data.toString()}`)
        if (data.toString().includes('Bridge ready')) {
            bridgeReady = true;
            checkAllProcessesReady();
        }
    })

    function checkAllProcessesReady() {
        if (serverReady && bridgeReady) {
            log.info('main.js - All backend processes are ready')
            clearTimeout(readinessTimeout);
        }
    }

    initializeReadinessCheck();

    bridgeProcess.stderr.on('data', (data) => {
        log.error(`main.js - Bridge Error: ${data.toString()}`)
    })

    // skipcq: JS-0125
    const pyshell = new PythonShell('app.py', {
        mode: 'text',
        // skipcq: JS-0240
        pythonPath: pythonPath,
        pythonOptions: ['-u'],
        scriptPath: path.join(__dirname, '../src/python')  // Points to src/python directory
    });

    // skipcq: JS-0241
    pyshell.on('error', function (err) {
        log.error('main.js - Flask server error:', err);
    });
}

app.on('before-quit', () => {
    log.info('main.js - Application shutting down');
    if (serverProcess) serverProcess.kill()
    if (bridgeProcess) bridgeProcess.kill()
    log.info('main.js - Backend processes terminated');
})

function createWindow() {
    log.info('main.js - Creating main window');
    startBackendProcesses()
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    })
    mainWindow.loadFile('src/index.html')
    log.info('main.js - Main window created and loaded');
}

app.whenReady().then(() => {
    log.info('main.js - Application ready, starting up...');
    createWindow();
})

app.on('window-all-closed', () => {
    log.info('main.js - All windows closed');
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

const { ipcMain } = require('electron')
const log = require('electron-log')

// Get todos handler
ipcMain.handle('get-todos', async (event) => {
    log.info('main.js - Handling get-todos request')
    try {
        // TODO: Implement your backend logic here
        return []
    } catch (error) {
        log.error('Error getting todos:', error)
        throw error
    }
})

// Add todo handler
ipcMain.handle('add-todo', async (event, todo) => {
    log.info('main.js - Handling add-todo request:', todo)
    try {
        // TODO: Implement your backend logic here
        return todo
    } catch (error) {
        log.error('Error adding todo:', error)
        throw error
    }
})

// Update todo handler
ipcMain.handle('update-todo', async (event, todo) => {
    log.info('main.js - Handling update-todo request:', todo)
    try {
        // TODO: Implement your backend logic here
        return todo
    } catch (error) {
        log.error('Error updating todo:', error)
        throw error
    }
})

// Delete todo handler
ipcMain.handle('delete-todo', async (event, id) => {
    log.info('main.js - Handling delete-todo request:', id)
    try {
        // TODO: Implement your backend logic here
        return id
    } catch (error) {
        log.error('Error deleting todo:', error)
        throw error
    }
})
