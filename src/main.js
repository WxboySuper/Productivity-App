const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const log = require('electron-log')
const { PythonShell } = require('python-shell');
const pythonPath = process.env.PYTHON_PATH || 'python'

let serverProcess = null
let bridgeProcess = null
let pyshell = null

function startBackendProcesses() {
    const userDataPath = app.getPath('userData')
    const dbPath = path.join(userDataPath, 'todo.db')
    
    const baseDir = app.isPackaged 
        ? path.join(process.resourcesPath, 'src', 'python')
        : path.join(__dirname, '../src/python')
        
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')

    try {  
        serverProcess = spawn(pythonPath, [serverScript], {  
            env: { ...process.env, DB_PATH: dbPath }  
        })  
     } catch (error) {  
         log.error(`Failed to start server process: ${error}`)  
         app.quit()  
     }     

     try {  
            bridgeProcess = spawn(pythonPath, [bridgeScript], {  
                env: { ...process.env, DB_PATH: dbPath }  
            })  
        } catch (error) {  
            log.error(`Failed to start bridge process: ${error}`)  
            app.quit()  
        }

    serverProcess.stdout.on('data', (data) => {
        const output = data.toString();  
        log.info(`Server: ${output}`)  
        if (output.includes('Running on')) {
            log.info('Flask server started successfully')
        }
    })

    serverProcess.stderr.on('data', (data) => {
        log.error(`Server Error: ${data}`)
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        log.info(`Bridge: ${data}`)
    })

    bridgeProcess.stderr.on('data', (data) => {  
        log.error(`Bridge Error: ${data}`)  
    }) 

    // skipcq: JS-0241
    pyshell = new PythonShell('app.py', {
        mode: 'text',
        // skipcq: JS-0240
        pythonPath: pythonPath,
        pythonOptions: ['-u'],
        scriptPath: app.isPackaged 
            ? path.join(process.resourcesPath, 'src', 'python')  
            : path.join(__dirname, '../src/python')
    });

    pyshell.on('error', err => {
        log.error('Flask server error:', err);
    });
}

function terminateProcesses() {
    if (serverProcess) {
        serverProcess.kill()
        log.info('Server process terminated')
    }
    
    if (bridgeProcess) {
        bridgeProcess.kill()
        log.info('Bridge process terminated')
    }
    
    if (pyshell) {
        pyshell.kill()
        log.info('Python shell terminated')
    }
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

app.on('before-quit', () => {
    terminateProcesses()
})