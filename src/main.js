const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const log = require('electron-log')

function startBackendProcesses() {
    const userDataPath = app.getPath('userData')
    const dbPath = path.join(userDataPath, 'todo.db')
    
    // Get the base directory for Python scripts
    const baseDir = app.isPackaged 
        ? path.join(path.dirname(app.getPath('exe')), 'src', 'python')
        : path.join(__dirname, '../src/python')
        
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')
    
    const pythonPath = app.isPackaged
        ? path.join(process.resourcesPath, 'python', 'python.exe')
        : 'python'

    const serverProcess = spawn(pythonPath, [serverScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })

    const bridgeProcess = spawn(pythonPath, [bridgeScript], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })
    
    // Log output from both processes
    serverProcess.stdout.on('data', (data) => {
        log.info(`Server: ${data}`)
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        log.info(`Bridge: ${data}`)
    })
}function createWindow() {
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