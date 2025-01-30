const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const { log, logOperation } = require('./js/logging_config')
const { PythonShell } = require('python-shell')
const pythonPath = process.env.PYTHON_PATH || 'python'

let serverProcess = null
let bridgeProcess = null
let pyshell = null

// Enable hot reload in development
if (process.env.NODE_ENV === 'development') {
  try {
    require('electron-reloader')(module, {
      watchDir: path.join(__dirname, 'python'),
      ignore: [/todo\.db/, /\.git/, /\.github/, /node_modules/, /dist/]
    })
  } catch (err) {
    // Ignore reloader errors in production
  }
}

/**
 * Starts the Python backend processes (server, bridge, and pyshell)
 * Initializes the database path and handles process output/errors
 * @throws {Error} If server or bridge processes fail to start
 */
function startBackendProcesses() {
    const userDataPath = app.getPath('userData')
    const dbPath = path.join(userDataPath, 'todo_dev.db')
    
    const baseDir = app.isPackaged 
        ? path.join(process.resourcesPath, 'src', 'python')
        : path.join(__dirname, '../src/python')
        
    const serverScript = path.join(baseDir, 'server.py')
    const bridgeScript = path.join(baseDir, 'todo_bridge.py')

    logOperation('info', 'startBackendProcesses', { userDataPath, dbPath })

    // Update environment variables for development
    const env = {
        ...process.env,
        PYTHONPATH: baseDir,
        PYTHON_PATH: pythonPath,
        FLASK_ENV: 'development',
        FLASK_DEBUG: 'true',
        DB_PATH: dbPath
    }

    try {  
        serverProcess = spawn(pythonPath, [serverScript], { env })  
        logOperation('info', 'serverStarted', { script: serverScript })
     } catch (error) {  
         logOperation('error', 'serverStartFailed', {}, error)
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
        logOperation('info', 'serverOutput', { output })
        if (output.includes('Running on')) {
            log.info('Flask server started successfully')
        }
    })

    serverProcess.stderr.on('data', (data) => {
        logOperation('error', 'serverError', { error: data.toString() })
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

/**
 * Terminates all running Python processes
 * Cleans up server, bridge, and pyshell processes
 */
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

/**
 * Creates and configures the main application window
 * Initializes backend processes and loads the main HTML file
 */
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