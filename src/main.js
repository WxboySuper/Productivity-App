const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Early error logging setup
function getAppDataPath() {
    const userDataPath = app.getPath('userData');
    const logsPath = path.join(userDataPath, 'logs');
    try {
        if (!fs.existsSync(logsPath)) {
            fs.mkdirSync(logsPath, { recursive: true });
        }
    } catch (err) {
        console.error('Failed to create logs directory:', err);
    }
    return logsPath;
}

// Update LOG_FILE path for production
const LOG_FILE = path.join(getAppDataPath(), 'productivity.log');

// Add startup error logging
process.on('uncaughtException', (error) => {
    const errorMsg = `[${new Date().toISOString()}] [ERROR] Startup Error: ${error.message}\n${error.stack}\n`;
    try {
        fs.appendFileSync(LOG_FILE, errorMsg);
    } catch (e) {
        console.error('Failed to write startup error:', e);
    }
});

// Setup logging first
function logToFile(level, message) {
    const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] electron - ${JSON.stringify(message)}\n`;
    
    try {
        fs.appendFileSync(LOG_FILE, logEntry);
    } catch (error) {
        console.error('Failed to write to log file:', error);
    }
}

// Set up IPC handler for logging
ipcMain.on('log-message', (_event, { level, message }) => {
    logToFile(level, message);
});

let pythonProcess = null;

function generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Update Python path resolution for packaged app
function getPythonPath() {
    const isPackaged = app.isPackaged;
    const resourcesPath = isPackaged ? process.resourcesPath : __dirname;
    const pythonPath = path.join(resourcesPath, 'python');
    const sitePackagesPath = path.join(pythonPath, 'lib', 'site-packages');
    
    return {
        scriptPath: path.join(pythonPath, 'server.py'),
        pythonPath: process.env.PYTHON_PATH || 'python',
        env: {
            ...process.env,
            PYTHONPATH: `${pythonPath}${path.delimiter}${sitePackagesPath}`
        }
    };
}

function startPythonServer() {
    return new Promise((resolve, reject) => {
        const { scriptPath, pythonPath, env } = getPythonPath();
        
        // Verify paths exist
        try {
            if (!fs.existsSync(scriptPath)) {
                throw new Error(`Server script not found at: ${scriptPath}`);
            }
            logToFile('debug', { 
                message: 'Starting server with paths',
                scriptPath,
                pythonPath,
                pythonPaths: env.PYTHONPATH
            });
        } catch (err) {
            logToFile('error', {
                message: 'Failed to verify paths',
                error: err.message
            });
            reject(err);
            return;
        }

        pythonProcess = spawn(pythonPath, [scriptPath], { env });

        // Listen for successful server startup
        const checkServer = () => {
            fetch('http://localhost:5000/health')
                .then(() => {
                    logToFile('info', 'pythonServerReady');
                    resolve();
                })
                .catch(() => {
                    // Keep checking until timeout
                    setTimeout(checkServer, 1000);
                });
        };

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            logToFile('debug', { output });
        });

        pythonProcess.stderr.on('data', (data) => {
            const output = data.toString();
            // Common Flask startup and operation messages that should be debug level
            const debugMessages = [
                'WARNING: This is a development server',
                'Running on http://',
                'Press CTRL+C to quit',
                '127.0.0.1 - -'
            ];
            
            if (debugMessages.some(msg => output.includes(msg))) {
                logToFile('debug', { output });
                if (output.includes('Running on http://')) {
                    checkServer();
                }
            } else {
                logToFile('error', { error: output });
            }
        });

        pythonProcess.on('error', (err) => {
            reject(new Error(`Failed to start Python server: ${err.message}`));
        });

        // Set a reasonable timeout
        setTimeout(() => {
            reject(new Error('Server startup timeout'));
        }, 30000);
    });
}

// Add IPC handlers
function setupIPCHandlers() {
    // Task operations
    ipcMain.handle('tasks:fetch', async () => {
        try {
            const response = await fetch('http://localhost:5000/tasks');
            return response.json();
        } catch (error) {
            logToFile('error', { operation: 'tasks:fetch', error: error.toString() });
            throw error;
        }
    });

    ipcMain.handle('tasks:add', async (_event, taskData) => {
        try {
            const response = await fetch('http://localhost:5000/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
            return response.json();
        } catch (error) {
            logToFile('error', { operation: 'tasks:add', error: error.toString() });
            throw error;
        }
    });

    // ...similar handlers for update and delete...
}

// Update createWindow to handle packaged paths
async function createWindow() {
    try {
        logToFile('info', 'startingPythonServer');
        await startPythonServer();

        logToFile('info', 'startingWindowCreation');
        
        const mainWindow = new BrowserWindow({
            width: 800,
            height: 600,
            webPreferences: {
                nodeIntegration: false,  // Disable Node integration
                contextIsolation: true,   // Keep context isolation enabled
                sandbox: true,           // Enable sandboxing
                preload: path.join(__dirname, 'preload.js'),
                webSecurity: true,  // Enable web security
                allowRunningInsecureContent: false,
                enableRemoteModule: false,
                devTools: true  // Always enable DevTools
            }
        });

        // Register keyboard shortcut for DevTools
        mainWindow.webContents.on('before-input-event', (event, input) => {
            if (input.control && input.shift && input.key.toLowerCase() === 'i') {
                logToFile('debug', 'DevTools opened via keyboard shortcut');
                mainWindow.webContents.openDevTools();
                event.preventDefault();
            }
        });

        const indexPath = app.isPackaged 
            ? path.join(__dirname, 'index.html')  // Changed from process.resourcesPath
            : path.join(__dirname, 'index.html');

        logToFile('info', { 
            path: indexPath,
            isPackaged: app.isPackaged,
            dirname: __dirname,
            resourcePath: process.resourcesPath
        });
        
        try {
            await mainWindow.loadFile(indexPath);
            mainWindow.show();
            
            if (process.env.NODE_ENV === 'development') {
                mainWindow.webContents.openDevTools();
            }
            
            logToFile('info', 'windowCreatedSuccessfully');
        } catch (loadError) {
            logToFile('error', { path: indexPath, error: loadError.toString() });
            throw loadError;
        }
        
    } catch (error) {
        logToFile('error', {
            operation: 'createWindow',
            error: error.message,
            stack: error.stack
        });
        app.quit();
    }
}
app.whenReady().then(() => {
    setupIPCHandlers();
    createWindow().catch(error => {
        logToFile('error', { operation: 'appInitializationFailed', error: error.toString() });
        app.quit();
    });
});

app.on('window-all-closed', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

process.on('uncaughtException', (error) => {
    logToFile('error', {
        requestId: generateRequestId(),
        operation: 'uncaughtException',
        timestamp: new Date().toISOString(),
        error: error.toString(),
        stack: error.stack
    });
});

// Enhanced error handling
process.on('unhandledRejection', (reason) => {
    logToFile('error', {
        requestId: generateRequestId(),
        operation: 'unhandledRejection',
        error: reason?.toString(),
        stack: reason?.stack
    });
});