const { contextBridge, ipcRenderer } = require('electron');

// Expose minimal API surface
contextBridge.exposeInMainWorld('electronAPI', {
    // Logging
    logger: {
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
                error: error ? { message: error.message, stack: error.stack } : null
            };
            ipcRenderer.send('log-message', { level, message });
        }
    },
    
    // Task operations
    tasks: {
        fetch: () => ipcRenderer.invoke('tasks:fetch'),
        add: (taskData) => ipcRenderer.invoke('tasks:add', taskData),
        update: (id, data) => ipcRenderer.invoke('tasks:update', id, data),
        delete: (id) => ipcRenderer.invoke('tasks:delete', id)
    }
});
