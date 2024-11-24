const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const log = require('electron-log')
const { PythonShell } = require('python-shell');
const pythonPath = 'python'

function startBackendProcesses() {
    const userDataPath = app.getPath('userData')
    const dbPath = path.join(userDataPath, 'todo.db')
    
    // Get the base directory for Python scripts
    const baseDir = app.isPackaged 
        ? path.join(process.resourcesPath, 'src', 'python')
        : path.join(__dirname, '../src/python')
        
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')

    log.info('Python scripts directory:', baseDir)
    log.info('Server script path:', serverScript)

    const serverProcess = spawn(pythonPath, [serverScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })

    serverProcess.stdout.on('data', (data) => {
        const message = data.toString();
        log.info(`Server: ${message}`)
        if (message.includes('Running on')) {
            log.info('Flask server started successfully')
        }
    })

    serverProcess.stderr.on('data', (data) => {
        log.error(`Server Error: ${data.toString()}`)
    })

    const bridgeProcess = spawn(pythonPath, [bridgeScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        log.info(`Bridge: ${data.toString()}`)
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

function createWindow() {
    startBackendProcesses()
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            // skipcq: JS-S1019
            nodeIntegration: true,
            // skipcq: JS-S1020
            contextIsolation: false
        }
    })
    mainWindow.loadFile('src/index.html')
}
app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
