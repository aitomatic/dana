// Enhanced Dana syntax highlighting for markdown preview
(function() {
    console.log('🎨 Dana syntax highlighting script loading...');
    
    // Check if we're in a VSCode/Cursor markdown preview
    const isVSCodePreview = typeof acquireVsCodeApi !== 'undefined' || 
                           window.location.protocol === 'vscode-webview-resource:' ||
                           document.querySelector('meta[name="vscode-preview"]');
    
    // Check if we're in Cursor specifically
    const isCursor = navigator.userAgent.includes('Cursor') || 
                    window.location.href.includes('cursor') ||
                    document.querySelector('meta[name="cursor-preview"]');
    
    // Check if we're in Markdown Preview Enhanced
    const isMarkdownPreviewEnhanced = document.querySelector('#mpe-preview') || 
                                     document.querySelector('.mpe-preview') ||
                                     window.location.href.includes('mpe-preview') ||
                                     document.querySelector('[data-mpe-preview]') ||
                                     document.querySelector('.markdown-preview-enhanced') ||
                                     document.querySelector('#markdown-preview-enhanced');
    
    console.log('🔍 Environment check:', {
        isVSCodePreview,
        isCursor,
        isMarkdownPreviewEnhanced,
        protocol: window.location.protocol,
        userAgent: navigator.userAgent.substring(0, 100),
        url: window.location.href.substring(0, 100)
    });

    // Token definitions with priority order (higher number = higher priority)
    const tokenDefinitions = [
        { type: 'comment', pattern: /#.*$/gm, priority: 100 },
        { type: 'fstring', pattern: /[fF]("""[\s\S]*?"""|'''[\s\S]*?'''|"[^"]*"|'[^']*')/g, priority: 90 },
        { type: 'string', pattern: /("""[\s\S]*?"""|'''[\s\S]*?'''|"[^"]*"|'[^']*')/g, priority: 85 },
        { type: 'number', pattern: /\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b/g, priority: 80 },
        { type: 'boolean', pattern: /\b(?:True|true|TRUE|False|false|FALSE|None|none|NONE|null|NULL)\b/g, priority: 75 },
        { type: 'type', pattern: /\b(?:int|float|str|bool|list|dict|tuple|set|any|void|object)\b/g, priority: 70 },
        { type: 'custom-type', pattern: /\b[A-Z][A-Za-z0-9_]*\b/g, priority: 65 },
        { type: 'keyword', pattern: /\b(?:if|elif|else|while|for|in|def|struct|interface|enum|try|except|finally|return|break|continue|pass|from|import|as|raise|assert|and|or|not|is|with|async|await|abstract|static|final|override)\b/g, priority: 60 },
        { type: 'builtin', pattern: /\b(?:len|sum|max|min|abs|round|sorted|reversed|enumerate|all|any|range|type|log|print|reason|use|set)\b/g, priority: 55 },
        { type: 'function', pattern: /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g, priority: 50 },
        { type: 'scope', pattern: /\b(?:private|public|system|local):/g, priority: 45 },
        { type: 'variable', pattern: /(?<=:)[a-zA-Z_][a-zA-Z0-9_]*/g, priority: 40 },
        { type: 'operator', pattern: /(?<![\w"'])(?:\*\*|\/\/|[+\-*/%=<>!&|^~]+)(?![\w"'])/g, priority: 35 },
        { type: 'punctuation', pattern: /[{}[\](),.:;]/g, priority: 30 }
    ];

    console.log('📝 Dana syntax patterns loaded:', tokenDefinitions.length, 'patterns');

    // Function to tokenize and highlight Dana code
    function highlightDana(code) {
        console.log('🎯 Highlighting Dana code block:', code.substring(0, 50) + (code.length > 50 ? '...' : ''));
        
        // Check if already processed
        if (code.includes('<span class="token')) {
            console.log('⚠️ Code already contains tokens, skipping processing');
            return code;
        }

        // Create a token array to store all matches
        const tokens = [];
        
        // Find all token matches and store them with their positions
        tokenDefinitions.forEach(def => {
            const regex = new RegExp(def.pattern.source, def.pattern.flags);
            let match;
            
            while ((match = regex.exec(code)) !== null) {
                tokens.push({
                    type: def.type,
                    text: match[0],
                    start: match.index,
                    end: match.index + match[0].length,
                    priority: def.priority,
                    capture: match[1] // For function names
                });
            }
        });

        // Sort tokens by priority (highest first) and then by position
        tokens.sort((a, b) => {
            if (a.priority !== b.priority) {
                return b.priority - a.priority;
            }
            return a.start - b.start;
        });

        // Remove overlapping tokens (keep the one with higher priority)
        const filteredTokens = [];
        for (const token of tokens) {
            let overlaps = false;
            for (const existing of filteredTokens) {
                if (token.start < existing.end && token.end > existing.start) {
                    overlaps = true;
                    break;
                }
            }
            if (!overlaps) {
                filteredTokens.push(token);
            }
        }

        // Sort tokens by position for processing
        filteredTokens.sort((a, b) => a.start - b.start);

        // Build the highlighted HTML
        let result = '';
        let lastIndex = 0;

        filteredTokens.forEach(token => {
            // Add text before this token
            result += code.substring(lastIndex, token.start);
            
            // Add the highlighted token
            const tokenText = token.capture || token.text;
            result += `<span class="token ${token.type}">${tokenText}</span>`;
            
            lastIndex = token.end;
        });

        // Add remaining text
        result += code.substring(lastIndex);

        console.log(`🎨 Total tokens highlighted: ${filteredTokens.length}`);
        return result;
    }

    // Function to process code blocks with enhanced selectors for Markdown Preview Enhanced
    function processCodeBlocks() {
        // Enhanced selectors for different markdown renderers including Markdown Preview Enhanced
        const selectors = [
            // Standard VSCode/Cursor selectors
            'code.language-dana',
            'pre code.language-dana',
            'code[class*="dana"]',
            'pre code[class*="dana"]',
            // Markdown Preview Enhanced specific selectors
            '.markdown-preview-enhanced code.language-dana',
            '.markdown-preview-enhanced pre code.language-dana',
            '#mpe-preview code.language-dana',
            '#mpe-preview pre code.language-dana',
            '.mpe-preview code.language-dana',
            '.mpe-preview pre code.language-dana',
            '[data-mpe-preview] code.language-dana',
            '[data-mpe-preview] pre code.language-dana',
            // Generic selectors that might work with MPE
            'code[data-lang="dana"]',
            'pre code[data-lang="dana"]',
            'code[data-language="dana"]',
            'pre code[data-language="dana"]',
            // Fallback: look for any code block containing Dana-like content
            'code:not(.dana-highlighted)',
            'pre code:not(.dana-highlighted)'
        ];
        
        let codeBlocks = [];
        let usedSelector = '';
        
        for (const selector of selectors) {
            const blocks = document.querySelectorAll(selector);
            if (blocks.length > 0) {
                // Filter blocks that look like Dana code
                const danaBlocks = Array.from(blocks).filter(block => {
                    const text = block.textContent || block.innerText;
                    // Check if it contains Dana-like patterns
                    return text.includes('def ') || 
                           text.includes('struct ') || 
                           text.includes('reason(') ||
                           text.includes('private:') ||
                           text.includes('public:') ||
                           text.includes('system:') ||
                           text.includes('local:') ||
                           text.includes('if ') ||
                           text.includes('for ') ||
                           text.includes('while ') ||
                           text.includes('return ') ||
                           text.includes('print(') ||
                           text.includes('log(') ||
                           text.includes('use ') ||
                           text.includes('set ') ||
                           text.includes('|') ||
                           text.includes('^') ||
                           text.includes('#') ||
                           block.classList.contains('language-dana') ||
                           block.getAttribute('data-lang') === 'dana' ||
                           block.getAttribute('data-language') === 'dana';
                });
                
                if (danaBlocks.length > 0) {
                    codeBlocks = danaBlocks;
                    usedSelector = selector;
                    console.log(`🔍 Found ${codeBlocks.length} Dana code blocks using selector: ${selector}`);
                    break;
                }
            }
        }
        
        if (codeBlocks.length === 0) {
            console.log('⚠️ No Dana code blocks found. Make sure to use ```dana in your markdown');
            console.log('🔍 Available code blocks:', document.querySelectorAll('code').length);
            console.log('🔍 Available pre blocks:', document.querySelectorAll('pre').length);
            
            // Debug: show all code blocks and their classes
            const allCodeBlocks = document.querySelectorAll('code');
            allCodeBlocks.forEach((block, index) => {
                console.log(`  Code block ${index}: classes="${block.className}", text="${block.textContent.substring(0, 30)}..."`);
            });
            return;
        }
        
        codeBlocks.forEach((block, index) => {
            // Only process if not already processed
            if (!block.classList.contains('dana-highlighted')) {
                console.log(`🎯 Processing Dana code block ${index + 1}/${codeBlocks.length} (selector: ${usedSelector})`);
                block.classList.add('dana-highlighted');
                
                // Get the original text content
                const originalText = block.textContent || block.innerText;
                const highlightedHtml = highlightDana(originalText);
                
                // Set the HTML content
                block.innerHTML = highlightedHtml;
                console.log(`✅ Dana code block ${index + 1} highlighted successfully`);
            } else {
                console.log(`⏭️ Dana code block ${index + 1} already highlighted, skipping`);
            }
        });
    }

    // Process code blocks on page load
    console.log('🚀 Initial processing of Dana code blocks...');
    
    // Try immediate processing
    processCodeBlocks();
    
    // Also try after a short delay to ensure DOM is ready
    setTimeout(() => {
        console.log('⏰ Delayed processing of Dana code blocks...');
        processCodeBlocks();
    }, 100);
    
    // Try again after a longer delay for slower renderers (especially MPE)
    setTimeout(() => {
        console.log('⏰ Long delayed processing of Dana code blocks...');
        processCodeBlocks();
    }, 1000);
    
    // Additional delay for Markdown Preview Enhanced which might load slower
    if (isMarkdownPreviewEnhanced) {
        setTimeout(() => {
            console.log('⏰ MPE-specific delayed processing of Dana code blocks...');
            processCodeBlocks();
        }, 2000);
        
        setTimeout(() => {
            console.log('⏰ Final MPE processing of Dana code blocks...');
            processCodeBlocks();
        }, 5000);
    }

    // Process code blocks when content changes (for dynamic content)
    const observer = new MutationObserver((mutations) => {
        let hasRelevantChanges = false;
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                // Check if any of the added nodes contain Dana code blocks
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.querySelector && (
                            node.querySelector('code.language-dana') ||
                            node.querySelector('code[data-lang="dana"]') ||
                            node.querySelector('code[data-language="dana"]') ||
                            node.querySelector('code')
                        )) {
                            hasRelevantChanges = true;
                        }
                    }
                });
            }
        });
        
        if (hasRelevantChanges) {
            console.log('🔄 Content changed, reprocessing Dana code blocks...');
            processCodeBlocks();
        }
    });

    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    console.log('👀 Mutation observer started for dynamic content');

    // Add a global function for manual testing
    window.danaHighlightTest = function() {
        console.log('🧪 Manual test triggered');
        processCodeBlocks();
        return `Dana highlighting script is loaded. Found ${document.querySelectorAll('code.language-dana').length} Dana code blocks.`;
    };

    // Add a visual indicator that the script is loaded
    const indicator = document.createElement('div');
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 3px;
        font-size: 12px;
        z-index: 10000;
        opacity: 0.8;
        font-family: monospace;
    `;
    
    let indicatorText = 'Dana Highlight ✓';
    if (isCursor) indicatorText = 'Dana Highlight (Cursor) ✓';
    if (isMarkdownPreviewEnhanced) indicatorText = 'Dana Highlight (MPE) ✓';
    
    indicator.textContent = indicatorText;
    document.body.appendChild(indicator);
    
    // Remove indicator after 3 seconds
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }, 3000);

    console.log('🎉 Dana syntax highlighting script loaded successfully');
})(); 