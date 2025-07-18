"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const path = require("path");
const node_1 = require("vscode-languageclient/node");
let client;
function activate(context) {
    console.log('Dana language extension is now active');
    // Start the Dana Language Server
    startLanguageServer(context);
    // Register the "Run Dana File" command
    const runFileCommand = vscode.commands.registerCommand('dana.runFile', () => {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            vscode.window.showErrorMessage('No active Dana file to run');
            return;
        }
        const document = activeEditor.document;
        // Check if it's a .na file
        if (!document.fileName.endsWith('.na')) {
            vscode.window.showErrorMessage('Please open a Dana (.na) file to run');
            return;
        }
        // Save the file if it has unsaved changes
        if (document.isDirty) {
            document.save();
        }
        // Create a new terminal and run the Dana file
        const terminal = vscode.window.createTerminal('Dana');
        terminal.show();
        // Try to use local Dana CLI first, fallback to PATH
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        let danaCommand = 'dana';
        if (workspaceRoot) {
            const localDana = `${workspaceRoot}/bin/dana`;
            // Check if we're in the Dana project (has bin/dana)
            try {
                const fs = require('fs');
                if (fs.existsSync(localDana)) {
                    danaCommand = localDana;
                }
            }
            catch (e) {
                // Fallback to 'dana' in PATH
            }
        }
        terminal.sendText(`"${danaCommand}" "${document.fileName}"`);
    });
    context.subscriptions.push(runFileCommand);
}
exports.activate = activate;
function startLanguageServer(context) {
    // Find the Dana Language Server command
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    let serverCommand = 'dana-ls';
    if (workspaceRoot) {
        // Try to use the local Dana installation first
        const localDanaLs = path.join(workspaceRoot, 'bin', 'dana-ls');
        const fs = require('fs');
        try {
            if (fs.existsSync(localDanaLs)) {
                serverCommand = localDanaLs;
            }
        }
        catch (e) {
            // Fallback to dana-ls in PATH
        }
    }
    // Configure the server options
    const serverOptions = {
        command: serverCommand,
        args: [],
        options: {
            cwd: workspaceRoot
        }
    };
    // Configure the client options
    const clientOptions = {
        // Register the server for Dana files
        documentSelector: [
            { scheme: 'file', language: 'dana' },
            { scheme: 'file', pattern: '**/*.na' }
        ],
        synchronize: {
            // Notify the server about file changes to Dana files
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.na')
        },
        outputChannelName: 'Dana Language Server'
    };
    // Create the language client
    client = new node_1.LanguageClient('dana-language-server', 'Dana Language Server', serverOptions, clientOptions);
    // Start the client and server
    client.start().then(() => {
        console.log('Dana Language Server started successfully');
    }).catch(error => {
        console.error('Failed to start Dana Language Server:', error);
        vscode.window.showWarningMessage('Dana Language Server failed to start. Advanced features may not be available. ' +
            'Make sure Dana is properly installed with: pip install lsprotocol pygls');
    });
    context.subscriptions.push({
        dispose: () => {
            if (client) {
                client.stop();
            }
        }
    });
}
function deactivate() {
    console.log('Dana language extension is now deactivated');
    if (!client) {
        return undefined;
    }
    return client.stop();
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map