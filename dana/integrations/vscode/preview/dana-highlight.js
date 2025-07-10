// Dana syntax highlighting for markdown preview
(function() {
    const danaSyntax = {
        // Keywords
        'keyword': /\b(if|elif|else|while|for|in|def|struct|interface|enum|try|except|finally|return|break|continue|pass|from|import|as|raise|assert|and|or|not|is|with|async|await)\b/,
        'boolean': /\b(True|true|TRUE|False|false|FALSE|None|none|NONE|null|NULL)\b/,
        'type': /\b(int|float|str|bool|list|dict|tuple|set|any|void|object)\b|\b[A-Z][A-Za-z0-9_]*\b/,
        'string': /("""[\s\S]*?"""|'''[\s\S]*?'''|"[^"]*"|'[^']*')/,
        'comment': /#.*/,
        'number': /\b\d+(\.\d+)?([eE][+-]?\d+)?\b/,
        'operator': /[-+*/%=<>!&|^~]+/,
        'punctuation': /[{}[\](),.:]/
    };

    // Function to apply syntax highlighting
    function highlightDana(code) {
        let html = code;
        for (const [type, regex] of Object.entries(danaSyntax)) {
            html = html.replace(regex, match => `<span class="token ${type}">${match}</span>`);
        }
        return html;
    }

    // Add styles for syntax highlighting
    const style = document.createElement('style');
    style.textContent = `
        .token.keyword { color: #569CD6; }
        .token.boolean { color: #569CD6; }
        .token.type { color: #4EC9B0; }
        .token.string { color: #CE9178; }
        .token.comment { color: #6A9955; }
        .token.number { color: #B5CEA8; }
        .token.operator { color: #D4D4D4; }
        .token.punctuation { color: #D4D4D4; }
    `;
    document.head.appendChild(style);

    // Find and highlight all Dana code blocks
    const codeBlocks = document.querySelectorAll('code.language-dana');
    codeBlocks.forEach(block => {
        block.innerHTML = highlightDana(block.textContent);
    });
})(); 