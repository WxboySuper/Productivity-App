const { spawn } = require('child_process');
const electron = require('electron');
const path = require('path');
const fs = require('fs');

// Setup logging
const LOG_FILE = path.join(__dirname, '..', 'logs', 'productivity.log');

function logToFile(level, message) {
    const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] electron - ${JSON.stringify(message)}\n`;
    try {
        fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    } catch (error) {
        // If we can't log to file, fall back to console as last resort
        console.error('Failed to write to log file:', error);
    }
}

// Get the base directory for Python files
const baseDir = path.join(__dirname);
const pythonPath = process.env.PYTHON_PATH || 'python';

// Set Python environment with correct PYTHONPATH
const env = {
    ...process.env,
    PYTHONPATH: baseDir,
    PYTHON_PATH: pythonPath,
    NODE_ENV: process.env.NODE_ENV || 'development'
};

let pythonProcess = null;

function startPythonServer() {
    const serverScript = path.join(__dirname, 'python', 'server.py');
    const isWindows = process.platform === 'win32';
    
    return new Promise((resolve, reject) => {
        // On Windows, use Flask's built-in server with production settings
        // On Unix systems, use Gunicorn
        if (isWindows) {
            pythonProcess = spawn(pythonPath, [serverScript], {
                env: {
                    ...env,
                    PYTHONPATH: path.join(__dirname, 'python'),
                    FLASK_ENV: 'production',
                    FLASK_DEBUG: 'false',
                    USE_PRODUCTION_SERVER: 'false'  // Signal to use Flask server
                }
            });
        } else {
            const gunicornBin = 'gunicorn';
            const gunicornPath = path.join(path.dirname(process.env.PYTHON_PATH || pythonPath), gunicornBin);
            
            pythonProcess = spawn(gunicornPath, [
                '--chdir', path.join(__dirname, 'python'),
                'server:app',
                '--bind', 'localhost:5000',
                '--workers', '1',
                '--timeout', '30',
                '--log-level', 'info'
            ], {
                env: {
                    ...env,
                    PYTHONPATH: path.join(__dirname, 'python'),
                    FLASK_ENV: 'production',
                    FLASK_DEBUG: 'false'
                }
            });
        }

        const startupTimeout = setTimeout(() => {
            reject(new Error('Server startup timeout after 45 seconds'));
        }, 45000);

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString();
            logToFile('debug', { component: 'python', output });
            if (output.includes('Listening at: http://localhost:5000')) {
                clearTimeout(startupTimeout);
                // Add small delay to ensure server is ready
                setTimeout(resolve, 1000);
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            const output = data.toString();
            logToFile('error', { component: 'python', error: output });
            if (output.includes('Booting worker with pid:')) {
                // Worker started, check if server is responsive
                fetch('http://localhost:5000/health')
                    .then(() => {
                        clearTimeout(startupTimeout);
                        resolve();
                    })
                    .catch(() => {/* Continue waiting */});
            }
        });

        pythonProcess.on('error', (err) => {
            logToFile('error', { 
                component: 'python',
                operation: 'serverStart',
                error: err.message,
                stack: err.stack
            });
            reject(new Error(`Failed to start server: ${err.message}`));
        });

        pythonProcess.on('exit', (code) => {
            if (code !== 0) {
                clearTimeout(startupTimeout);
                reject(new Error(`Server process exited with code ${code}`));
            }
        });
    });
}

function startElectron() {
    return new Promise((resolve, reject) => {
        const electronProcess = spawn(electron, ['.'], {
            stdio: 'inherit',
            env: {
                ...process.env,
                ELECTRON_START_URL: 'http://localhost:5000'
            }
        });

        electronProcess.on('error', (err) => {
            reject(err);
        });

        electronProcess.on('exit', (code) => {
            if (code !== 0) {
                reject(new Error(`Electron exited with code ${code}`));
            }
        });

        resolve(electronProcess);
    });
}

// Main startup sequence
async function start() {
    try {
        logToFile('info', { operation: 'startup', message: 'Starting Python server...' });
        await startPythonServer();
        logToFile('info', { operation: 'startup', message: 'Server started successfully' });
        
        logToFile('info', { operation: 'startup', message: 'Starting Electron...' });
        await startElectron();
        logToFile('info', { operation: 'startup', message: 'Electron started successfully' });
    } catch (error) {
        logToFile('error', {
            operation: 'startup',
            error: error.message,
            stack: error.stack
        });
        if (pythonProcess) pythonProcess.kill();
        process.exit(1);
    }
}

process.on('uncaughtException', (error) => {
    logToFile('error', {
        operation: 'uncaughtException',
        error: error.message,
        stack: error.stack
    });
});

process.on('unhandledRejection', (reason) => {
    logToFile('error', {
        operation: 'unhandledRejection',
        error: reason?.toString(),
        stack: reason?.stack
    });
});

start();
