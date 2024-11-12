const { app, BrowserWindow } = require('electron')
// skipcq: JS-0128
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 1600,
        height: 1000,
        webPreferences: {
            // skipcq: JS-S1019
            nodeIntegration: true,
            // skipcq: JS-S1020
            contextIsolation: false
        }
    })

    win.loadFile('src/index.html')
    
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