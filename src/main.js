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
    log.info('User data path:', userDataPath);
    
    const dbPath = path.join(userDataPath, 'todo.db');
    log.info('Database path:', dbPath);
    
    const baseDir = app.isPackaged 
        ? path.join(process.resourcesPath, 'src', 'python')
        : path.join(__dirname, '../src/python');
    
    log.info('Base directory:', baseDir);
    log.info('Python executable:', pythonPath);
    
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')

    log.info('Python scripts directory:', baseDir)
    log.info('Server script path:', serverScript)

    serverProcess = spawn(pythonPath, [serverScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    }).on('error', (err) => {
        log.error('Failed to start server process:', err)
    })

    let serverReady = false
    let bridgeReady = false

    serverProcess.stdout.on('data', (data) => {
        log.info(`Server output: ${data}`);
        if (data.toString().includes('Running on')) {
            log.info('Flask server started successfully')
            serverReady = true;
            checkAllProcessesReady()
        }
    })

    serverProcess.stderr.on('data', (data) => {
        log.error(`Server Error: ${data.toString()}`)
    })

    bridgeProcess = spawn(pythonPath, [bridgeScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        log.info(`Bridge: ${data.toString()}`)
        if (data.toString().includes('Bridge ready')) {
            bridgeReady = true;
            checkAllProcessesReady();
        }
    })

    function checkAllProcessesReady() {
        if (serverReady && bridgeReady) {
            log.info('All backend processes are ready')
        }
    }

    bridgeProcess.stderr.on('data', (data) => {
        log.error(`Bridge Error: ${data.toString()}`)
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
        // skipcq: JS-0002
        console.log('Flask server error:', err);
    });
}

app.on('before-quit', () => {
    log.info('Application shutting down');
    if (serverProcess) serverProcess.kill()
    if (bridgeProcess) bridgeProcess.kill()
    log.info('Backend processes terminated');
})

function createWindow() {
    log.info('Creating main window');
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
    log.info('Main window created and loaded');
}

app.whenReady().then(() => {
    log.info('Application ready, starting up...');
    createWindow();
})

app.on('window-all-closed', () => {
    log.info('All windows closed');
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
