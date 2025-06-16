const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let backendProcess;
let mainWindow;

function startBackend() {
    const backendPath = path.join(__dirname, 'backend', 'dist', 'fastapibackend.exe');

    if (!fs.existsSync(backendPath)) {
        dialog.showErrorBox(
            'Backend Error',
            `Backend executable not found at: ${backendPath}\nPlease ensure you have built your Python backend with PyInstaller.`
        );
        app.quit();
        return;
    }

    backendProcess = spawn(backendPath);

    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });

    backendProcess.on('error', (err) => {
        console.error(`Failed to start backend process: ${err.message}`);
        dialog.showErrorBox(
            'Backend Launch Error',
            `Could not start the backend application. Error: ${err.message}`
        );
        app.quit();
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Load your frontend application
    const frontendPath = path.join(__dirname, 'frontend', 'dist', 'index.html');
    console.log(`Loading frontend from: ${frontendPath}`);
    
    // Check if the frontend build exists
    if (fs.existsSync(frontendPath)) {
        mainWindow.loadFile(frontendPath);
    } else {
        dialog.showErrorBox(
            'Frontend Build Missing',
            `Frontend build not found at ${frontendPath}. Please run 'npm run build' in your 'frontend/' directory.`
        );
        app.quit();
    }

    // Open the DevTools to see any console errors from the frontend
    mainWindow.webContents.openDevTools(); 
}

app.on('ready', () => {
    startBackend();
    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', () => {
    if (backendProcess) {
        console.log('Terminating backend process...');
        backendProcess.kill('SIGTERM'); 
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});