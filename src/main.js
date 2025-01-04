const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Setup logging first
const LOG_FILE = path.join(__dirname, '..', 'logs', 'productivity.log');

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

function startPythonServer() {
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const serverScript = path.join(__dirname, 'python', 'server.py');
    
    return new Promise((resolve, reject) => {
        pythonProcess = spawn(pythonPath, [serverScript], {
            env: {
                ...process.env,
                PYTHONPATH: path.join(__dirname, 'python')  // Fix Python path
            }
        });

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

async function createWindow() {
    try {
        logToFile('info', 'startingPythonServer');
        await startPythonServer();

        logToFile('info', 'startingWindowCreation');
        
        const mainWindow = new BrowserWindow({
            width: 800,
            height: 600,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: true,
                enableRemoteModule: true,
                preload: path.join(__dirname, 'preload.js'),
                sandbox: false
            }
        });

        const indexPath = path.join(__dirname, 'index.html');
        logToFile('info', { path: indexPath });
        
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
        logToFile('error', { operation: 'serverStartFailed', error: error.toString() });
        app.quit();
    }
}

app.whenReady().then(() => {
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