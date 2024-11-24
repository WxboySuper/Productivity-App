const { contextBridge, ipcRenderer } = require('electron')
const log = require('electron-log')

// Configure production logging
log.transports.file.level = process.env.NODE_ENV === 'production' ? 'info' : 'debug'
log.transports.file.maxSize = 10 * 1024 * 1024 // 10MB
log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}] [{level}] {text}'
log.info('preload.js - Preload script initializing')

// Define the API methods
const api = {
    getTodos: async () => {
        log.info('preload.js - getTodos called from renderer')
        // skipcq: JS-0111
        return await ipcRenderer.invoke('get-todos')
    },
    addTodo: async (todo) => {
        log.info('preload.js - addTodo called with:', todo)
        // skipcq: JS-0111
        return await ipcRenderer.invoke('add-todo', todo)
    },
    updateTodo: async (todo) => {
        log.info('preload.js - updateTodo called with:', todo)
        // skipcq: JS-0111
        return await ipcRenderer.invoke('update-todo', todo)
    },
    deleteTodo: async (id) => {
        log.info('preload.js - deleteTodo called with id:', id)
        // skipcq: JS-0111
        return await ipcRenderer.invoke('delete-todo', id)
    }
}

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('api', api)
log.info('API exposed to renderer process')