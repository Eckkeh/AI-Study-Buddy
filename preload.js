const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    sendText: (text) => ipcRenderer.invoke('send-text', text),
    sendPdf: (pdfBytes) => ipcRenderer.invoke('send-pdf', pdfBytes),
});