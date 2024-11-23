const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

function startBackendProcesses() {
    const userDataPath = app.getPath('userData')
    const dbPath = path.join(userDataPath, 'todo.db')
    
    // Get the base directory for executables
    const baseDir = app.isPackaged 
        ? path.dirname(app.getPath('exe'))
        : path.join(__dirname, '../dist')
        
    const serverPath = path.join(baseDir, 'server.exe')
    const bridgePath = path.join(baseDir, 'todo_bridge.exe')
    
    const serverProcess = spawn(serverPath, [], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })
    
    const bridgeProcess = spawn(bridgePath, [], {
        env: {
            ...process.env,
            DB_PATH: dbPath
        }
    })
    
    // Log output from both processes
    serverProcess.stdout.on('data', (data) => {
        // skipcq: JS-0002
        console.log(`Server: ${data}`)
    })
    
    bridgeProcess.stdout.on('data', (data) => {
        // skipcq: JS-0002
        console.log(`Bridge: ${data}`)
    })
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