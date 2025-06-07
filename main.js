const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess;

console.log("Main process started"); 

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    win.loadFile('index.html');
}

app.whenReady().then(() => {
    pythonProcess = spawn('python', ['backend/app.py']);
    createWindow();
});

app.on('window-all-closed', () => {
    if (pythonProcess) pythonProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('send-text', async (event, inputText) => {
    const response = await fetch('http://127.0.0.1:5000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
    });
    return await response.json();
});

ipcMain.handle('send-pdf', async (event, pdfBytes) => {
    const response = await fetch('http://127.0.0.1:5000/process-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: Buffer.from(pdfBytes),
    });
    return await response.json();
});
