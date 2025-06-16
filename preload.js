const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    sendText: (text, quizType) => ipcRenderer.invoke('send-text', text, quizType),
    sendPdf: (pdfBytes, quizType) => ipcRenderer.invoke('send-pdf', pdfBytes, quizType),
});