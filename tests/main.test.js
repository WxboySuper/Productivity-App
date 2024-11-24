const { app, ipcMain } = require('electron');

jest.mock('electron', () => ({
    app: {
        on: jest.fn(),
        whenReady: jest.fn()
    },
    ipcMain: {
        handle: jest.fn()
    }
}));

describe('Main Process', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('registers all IPC handlers on startup', () => {
        require('../src/main');
        expect(ipcMain.handle).toHaveBeenCalledWith('get-todos', expect.any(Function));
        expect(ipcMain.handle).toHaveBeenCalledWith('add-todo', expect.any(Function));
        expect(ipcMain.handle).toHaveBeenCalledWith('update-todo', expect.any(Function));
        expect(ipcMain.handle).toHaveBeenCalledWith('delete-todo', expect.any(Function));
    });

    test('IPC handlers return expected results', async () => {
        const main = require('../src/main');
        
        // Get the handler functions
        const getTodosHandler = ipcMain.handle.mock.calls.find(call => call[0] === 'get-todos')[1];
        const addTodoHandler = ipcMain.handle.mock.calls.find(call => call[0] === 'add-todo')[1];
        
        // Test getTodos handler
        const todos = await getTodosHandler();
        expect(Array.isArray(todos)).toBe(true);
        
        // Test addTodo handler
        const newTodo = { title: 'Test Todo', completed: false };
        const result = await addTodoHandler({}, newTodo);
        expect(result).toEqual(newTodo);
    });

    test('app handles errors gracefully', async () => {
        const main = require('../src/main');
        const deleteHandler = ipcMain.handle.mock.calls.find(call => call[0] === 'delete-todo')[1];
        
        // Test error handling
        await expect(deleteHandler({}, null)).rejects.toThrow();
    });
});