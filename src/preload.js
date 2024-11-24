const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
    // Add any API methods you want to expose to the renderer process
    // For example:
    getTodos: () => ipcRenderer.invoke('get-todos'),
    addTodo: (todo) => ipcRenderer.invoke('add-todo', todo),
    updateTodo: (todo) => ipcRenderer.invoke('update-todo', todo),
    deleteTodo: (id) => ipcRenderer.invoke('delete-todo', id)
})
