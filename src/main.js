const { app, BrowserWindow } = require('electron')
// skipcq: JS-0128
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            // skipcq: JS-S1019
            nodeIntegration: true,
            // skipcq: JS-S1020
            contextIsolation: false
        }
    })

    win.loadFile('src/index.html')
    console.log('Window created and loaded')
    
    // Open DevTools automatically
    win.webContents.openDevTools()
}
app.whenReady().then(() => {
    createWindow()
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})