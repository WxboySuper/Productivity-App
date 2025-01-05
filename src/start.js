const { spawn } = require('child_process');
const electron = require('electron');
const path = require('path');

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

const serverProcess = null;
let pythonProcess = null;

function startElectron() {
    // Start Electron app
    const electronProcess = spawn(electron, ['.'], {
        stdio: 'inherit',
        env
    });

    electronProcess.on('error', (err) => {
        console.error('Failed to start Electron:', err);
        if (serverProcess) serverProcess.kill();
        process.exit(1);
    });

    // Handle process termination
    process.on('SIGTERM', () => {
        serverProcess.kill();
        electronProcess.kill();
    });

    process.on('exit', () => {
        serverProcess.kill();
        electronProcess.kill();
    });
}

function startPythonServer() {
    const gunicornBin = process.platform === 'win32' ? 'gunicorn.exe' : 'gunicorn';
    const gunicornPath = path.join(path.dirname(pythonPath), gunicornBin);
    
    return new Promise((resolve, reject) => {
        pythonProcess = spawn(gunicornPath, [
            'python.server:app',
            '--bind', 'localhost:5000',
            '--workers', '4',
            '--timeout', '120',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--capture-output',
            '--enable-stdio-inheritance'
        ], {
            env: {
                ...process.env,
                PYTHONPATH: path.join(__dirname, 'python'),
                FLASK_ENV: 'production',
                FLASK_DEBUG: 'false'
            }
        });
        
        pythonProcess.on('error', (err) => {
            console.error('Failed to start Python server:', err);
            reject(err);
        });

        pythonProcess.stdout.on('data', (data) => {
            if (data.toString().includes('Booting worker with pid')) {
                resolve();
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python server error: ${data}`);
        });
    });
}

try {
    startPythonServer().then(() => {
        // Start Electron after Python server is running
        startElectron();
    }).catch((error) => {
        console.error('Failed to start Python server:', error);
        process.exit(1);
    });
} catch (error) {
    console.error('Failed to start application:', error);
    process.exit(1);
}
