const { contextBridge, ipcRenderer } = require('electron');
const path = require('path');

// Expose protected methods that allow the renderer process to use
// specific electron APIs without exposing the entire API
contextBridge.exposeInMainWorld(
    'api', {
        node: () => process.versions.node,
        chrome: () => process.versions.chrome,
        electron: () => process.versions.electron,
        path: path.join,
        // Add other API methods you need
    }
);

// Expose logging functionality
contextBridge.exposeInMainWorld(
    'electronLogger', {
        log: (level, message) => ipcRenderer.send('log-message', { level, message }),
        info: (message) => ipcRenderer.send('log-message', { level: 'info', message }),
        error: (message) => ipcRenderer.send('log-message', { level: 'error', message }),
        warn: (message) => ipcRenderer.send('log-message', { level: 'warn', message }),
        debug: (message) => ipcRenderer.send('log-message', { level: 'debug', message }),
        logOperation: (level, operation, context = {}, error = null) => {
            const message = {
                requestId: `op_${Date.now()}`,
                operation,
                timestamp: new Date().toISOString(),
                context,
                error: error ? {
                    message: error.message,
                    stack: error.stack
                } : null
            };
            ipcRenderer.send('log-message', { level, message });
        }
    }
);
