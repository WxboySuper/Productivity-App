const { contextBridge, ipcRenderer } = require('electron');

jest.mock('electron', () => ({
  contextBridge: {
      exposeInMainWorld: jest.fn()
  },
  ipcRenderer: {
      invoke: jest.fn()
  }
}));

describe('Preload Script API', () => {
  beforeEach(() => {
      jest.clearAllMocks();
  });

  test('getTodos calls ipcRenderer.invoke with correct channel', async () => {
      const api = require('../src/preload');
      await api.getTodos();
      expect(ipcRenderer.invoke).toHaveBeenCalledWith('get-todos');
  });

  test('addTodo calls ipcRenderer.invoke with todo data', async () => {
      const api = require('../src/preload');
      const todo = { title: 'Test Todo', completed: false };
      await api.addTodo(todo);
      expect(ipcRenderer.invoke).toHaveBeenCalledWith('add-todo', todo);
  });

  test('updateTodo calls ipcRenderer.invoke with updated todo', async () => {
      const api = require('../src/preload');
      const todo = { id: 1, title: 'Updated Todo', completed: true };
      await api.updateTodo(todo);
      expect(ipcRenderer.invoke).toHaveBeenCalledWith('update-todo', todo);
  });

  test('deleteTodo calls ipcRenderer.invoke with todo id', async () => {
      const api = require('../src/preload');
      await api.deleteTodo(1);
      expect(ipcRenderer.invoke).toHaveBeenCalledWith('delete-todo', 1);
  });
});