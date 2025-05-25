import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Dana language extension is now active');

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
            } catch (e) {
                // Fallback to 'dana' in PATH
            }
        }
        
        terminal.sendText(`"${danaCommand}" "${document.fileName}"`);
    });

    context.subscriptions.push(runFileCommand);
}

export function deactivate() {
    console.log('Dana language extension is now deactivated');
} 