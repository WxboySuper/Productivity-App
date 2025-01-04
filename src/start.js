const { spawn } = require('child_process');
const electron = require('electron');
const path = require('path');

// Get the base directory for Python files
const baseDir = path.join(__dirname);
const pythonPath = process.env.PYTHON_PATH || 'python';
const serverScript = path.join(baseDir, 'python', 'server.py');

// Set Python environment with correct PYTHONPATH
const env = {
    ...process.env,
    PYTHONPATH: baseDir,
    PYTHON_PATH: pythonPath,
    NODE_ENV: process.env.NODE_ENV || 'development'
};

let serverProcess = null;

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

try {
    serverProcess = spawn(pythonPath, [serverScript], { env });
    serverProcess.on('error', (err) => {
        console.error('Failed to start Python server:', err);
        process.exit(1);
    });

    // Start Electron after Python server is running
    startElectron();
} catch (error) {
    console.error('Failed to start application:', error);
    process.exit(1);
}
