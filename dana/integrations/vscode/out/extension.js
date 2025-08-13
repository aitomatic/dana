"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const path = require("path");
// Make language server optional
let LanguageClient;
let LanguageClientOptions;
let ServerOptions;
try {
    const lsp = require('vscode-languageclient/node');
    LanguageClient = lsp.LanguageClient;
    LanguageClientOptions = lsp.LanguageClientOptions;
    ServerOptions = lsp.ServerOptions;
}
catch (error) {
    // Language server dependencies not available, LSP features disabled
}
let client;
function activate(context) {
    // Start the Dana Language Server only if available
    if (LanguageClient) {
        startLanguageServer(context);
    }
    // Register markdown preview enhancement
    registerMarkdownPreviewEnhancement(context);
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
    // Register a command to test Markdown Preview Enhanced integration
    const testMPECommand = vscode.commands.registerCommand('dana.testMPE', () => {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor || activeEditor.document.languageId !== 'markdown') {
            vscode.window.showErrorMessage('Please open a markdown file to test MPE integration');
            return;
        }
        // Create a test markdown file with Dana code blocks
        const testContent = `# Dana Syntax Highlighting Test for Markdown Preview Enhanced

This is a test of Dana syntax highlighting in Markdown Preview Enhanced.

## Basic Dana Code

\`\`\`dana
# Basic knowledge curation
context = {"domain": "general", "task": "knowledge_extraction"}
sources = ["./docs/api.md", "./docs/architecture.md"]
ecosystem = curate_knowledge_ecosystem(context, sources)
\`\`\`

## Dana Functions

\`\`\`dana
def analyze_defects(process_data: dict, equipment_logs: list) -> dict:
    """Analyze semiconductor defects from process data."""
    
    results = {
        "defect_count": 0,
        "critical_defects": [],
        "recommendations": []
    }
    
    for log in equipment_logs:
        if log.get("defect_detected", False):
            results["defect_count"] += 1
            
            if log["severity"] == "critical":
                results["critical_defects"].append(log)
    
    return results
\`\`\`

## Dana with Scopes

\`\`\`dana
private: user_data = {"name": "John", "age": 30}
public: config = {"api_key": "abc123", "endpoint": "https://api.example.com"}
system: logger = log("system", "info")

def process_user(user: dict) -> bool:
    if user.get("age", 0) >= 18:
        return True
    return False

result = process_user(user_data)
\`\`\`

## Dana with Pipes

\`\`\`dana
def double(x: int) -> int:
    return x * 2

def stringify(x: int) -> str:
    return str(x)

# Sequential pipeline
result1 = 5 | double | stringify

# Parallel pipeline
pipeline = double | [stringify, lambda x: x + 10]
result2 = pipeline(5)
\`\`\`

The highlighting should work automatically in Markdown Preview Enhanced. Look for the green "Dana Highlight (MPE) ✓" indicator in the top-right corner.`;
        // Create and show the test document
        const testUri = vscode.Uri.parse('untitled:test-dana-mpe.md');
        vscode.workspace.openTextDocument(testUri).then(doc => {
            vscode.window.showTextDocument(doc).then(editor => {
                editor.edit(editBuilder => {
                    editBuilder.insert(new vscode.Position(0, 0), testContent);
                });
                vscode.window.showInformationMessage('Dana MPE test created! Open Markdown Preview Enhanced to see syntax highlighting.');
            });
        });
    });
    context.subscriptions.push(runFileCommand, testMPECommand);
}
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
    client = new LanguageClient('dana-language-server', 'Dana Language Server', serverOptions, clientOptions);
    // Start the client and server
    client.start().then(() => {
        // Language server started successfully
    }).catch((error) => {
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
function registerMarkdownPreviewEnhancement(context) {
    // Register a markdown preview provider that enhances Dana code blocks
    const markdownPreviewProvider = vscode.workspace.registerTextDocumentContentProvider('dana-preview', {
        provideTextDocumentContent(uri) {
            // This is a placeholder - the actual enhancement is done via markdown.previewScripts
            return '';
        }
    });
    context.subscriptions.push(markdownPreviewProvider);
}
function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
//# sourceMappingURL=extension.js.map