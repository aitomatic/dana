#!/usr/bin/env node
/**
 * Cursor Chat History Cleaner
 */

const fs = require('fs');
const path = require('path');

class ChatHistoryCleaner {
    constructor() {
        this.projectKeywords = [
            'dana', 'lambda', 'promise', 'deliver', 'return', 'async', 'await',
            'executor', 'expression', 'statement', 'control', 'flow',
            'struct', 'function', 'agent', 'framework', 'poet', 'knows',
            'corral', 'memory', 'stdlib', 'corelib', 'api', 'router',
            'concurrency', 'parallel', 'gather', 'task', 'coroutine'
        ];
    }
    
    async processChatHistory(inputFile, options = {}) {
        console.log(`Processing: ${inputFile}`);
        
        try {
            const rawData = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
            console.log(`Loaded ${rawData.length} entries`);
            
            const filteredData = this.filterRelevantContent(rawData, options);
            console.log(`Filtered to ${filteredData.length} relevant entries`);
            
            const conversations = this.extractConversations(filteredData);
            console.log(`Extracted ${conversations.length} conversations`);
            
            const cleanedConversations = conversations.map(conv => 
                this.cleanConversation(conv, options)
            );
            
            const organizedContent = this.organizeByTopics(cleanedConversations);
            await this.generateOutputFiles(organizedContent, options);
            
            console.log('Processing completed!');
            
        } catch (error) {
            console.error('Error:', error);
            process.exit(1);
        }
    }
    
    filterRelevantContent(data, options) {
        const { keywords = this.projectKeywords, minLength = 10 } = options;
        
        return data.filter(entry => {
            const content = this.extractTextContent(entry.data);
            
            if (content.length < minLength) return false;
            
            const hasRelevantKeywords = keywords.some(keyword => 
                content.toLowerCase().includes(keyword.toLowerCase())
            );
            
            const hasCodeContent = /```[\w]*\n([\s\S]*?)\n```/g.test(content);
            
            return hasCodeContent || hasRelevantKeywords;
        });
    }
    
    extractTextContent(data) {
        if (typeof data === 'string') return data;
        
        if (typeof data === 'object' && data !== null) {
            const contentFields = ['content', 'text', 'message', 'data', 'value', 'body'];
            
            for (const field of contentFields) {
                if (data[field] && typeof data[field] === 'string') {
                    return data[field];
                }
            }
            
            for (const [key, value] of Object.entries(data)) {
                if (typeof value === 'string' && value.length > 50) {
                    return value;
                }
                if (typeof value === 'object' && value !== null) {
                    const nestedContent = this.extractTextContent(value);
                    if (nestedContent) return nestedContent;
                }
            }
        }
        
        return JSON.stringify(data);
    }
    
    extractConversations(data) {
        const conversations = [];
        let currentConversation = [];
        
        for (const entry of data) {
            const content = this.extractTextContent(entry.data);
            
            if (this.isNewConversation(content)) {
                if (currentConversation.length > 0) {
                    conversations.push({
                        entries: currentConversation,
                        summary: this.generateConversationSummary(currentConversation)
                    });
                }
                currentConversation = [];
            }
            
            currentConversation.push({
                content,
                metadata: {
                    database: entry.database,
                    table: entry.table,
                    timestamp: entry.timestamp,
                    matchedKeywords: entry.matched_keywords
                }
            });
        }
        
        if (currentConversation.length > 0) {
            conversations.push({
                entries: currentConversation,
                summary: this.generateConversationSummary(currentConversation)
            });
        }
        
        return conversations;
    }
    
    isNewConversation(content) {
        const patterns = [/^User:/, /^Assistant:/, /^Human:/, /^AI:/, /^---\s*$/, /^#+\s+/];
        return patterns.some(pattern => pattern.test(content));
    }
    
    generateConversationSummary(conversation) {
        const allContent = conversation.map(entry => entry.content).join(' ');
        const keywords = this.extractKeyTopics(allContent);
        
        return {
            topic: keywords.slice(0, 3).join(', '),
            keywords,
            entryCount: conversation.length,
            hasCode: /```[\w]*\n([\s\S]*?)\n```/g.test(allContent)
        };
    }
    
    extractKeyTopics(content) {
        const words = content.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 3);
        
        const wordCount = {};
        words.forEach(word => {
            wordCount[word] = (wordCount[word] || 0) + 1;
        });
        
        return Object.entries(wordCount)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([word]) => word);
    }
    
    cleanConversation(conversation, options) {
        const { removeMarkdown = true, preserveCode = true } = options;
        
        const cleanedEntries = conversation.entries.map(entry => {
            let cleanedContent = entry.content;
            
            if (removeMarkdown) {
                cleanedContent = this.removeMarkdownFormatting(cleanedContent, preserveCode);
            }
            
            cleanedContent = this.removeIrrelevantContent(cleanedContent);
            
            return {
                ...entry,
                content: cleanedContent.trim()
            };
        }).filter(entry => entry.content.length > 0);
        
        return {
            ...conversation,
            entries: cleanedEntries
        };
    }
    
    removeMarkdownFormatting(content, preserveCode = true) {
        let cleaned = content;
        
        if (preserveCode) {
            const codeBlocks = [];
            cleaned = cleaned.replace(/```[\w]*\n([\s\S]*?)\n```/g, (match, code) => {
                codeBlocks.push(code);
                return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
            });
            
            cleaned = cleaned
                .replace(/^#+\s+/gm, '')
                .replace(/\*\*(.*?)\*\*/g, '$1')
                .replace(/\*(.*?)\*/g, '$1')
                .replace(/`([^`]+)`/g, '$1')
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
                .replace(/^\s*[-*+]\s+/gm, '')
                .replace(/^\s*\d+\.\s+/gm, '')
                .replace(/^\s*>\s+/gm, '')
                .replace(/\n{3,}/g, '\n\n');
            
            codeBlocks.forEach((code, index) => {
                cleaned = cleaned.replace(`__CODE_BLOCK_${index}__`, code);
            });
        } else {
            cleaned = cleaned
                .replace(/```[\w]*\n[\s\S]*?\n```/g, '')
                .replace(/`[^`]+`/g, '')
                .replace(/^#+\s+/gm, '')
                .replace(/\*\*(.*?)\*\*/g, '$1')
                .replace(/\*(.*?)\*/g, '$1')
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
                .replace(/^\s*[-*+]\s+/gm, '')
                .replace(/^\s*\d+\.\s+/gm, '')
                .replace(/^\s*>\s+/gm, '')
                .replace(/\n{3,}/g, '\n\n');
        }
        
        return cleaned;
    }
    
    removeIrrelevantContent(content) {
        const irrelevantPatterns = [
            /^\s*$/,
            /^[^\w]*$/,
            /^(User|Assistant):\s*$/,
            /^```\s*$/,
            /^---\s*$/,
            /^#+\s*$/,
            /^\[.*\]\s*$/,
            /^\(\d+\)\s*$/,
            /^[A-Za-z0-9]{8,}\s*$/,
            /^[0-9a-f]{8,}\s*$/i,
        ];
        
        return content
            .split('\n')
            .filter(line => !irrelevantPatterns.some(pattern => pattern.test(line)))
            .join('\n');
    }
    
    organizeByTopics(conversations) {
        const topics = {
            'dana-core': [],
            'dana-frameworks': [],
            'dana-api': [],
            'dana-stdlib': [],
            'development-workflow': [],
            'debugging': [],
            'general': []
        };
        
        const topicKeywords = {
            'dana-core': ['lambda', 'promise', 'deliver', 'return', 'async', 'await', 'executor'],
            'dana-frameworks': ['poet', 'knows', 'corral', 'memory', 'agent', 'framework'],
            'dana-api': ['api', 'router', 'endpoint', 'server', 'client'],
            'dana-stdlib': ['stdlib', 'corelib', 'library', 'function'],
            'development-workflow': ['git', 'commit', 'branch', 'merge', 'pull', 'request'],
            'debugging': ['debug', 'error', 'fix', 'test', 'issue', 'bug']
        };
        
        conversations.forEach(conversation => {
            const content = conversation.entries.map(entry => entry.content).join(' ').toLowerCase();
            let categorized = false;
            
            for (const [topic, keywords] of Object.entries(topicKeywords)) {
                if (keywords.some(keyword => content.includes(keyword))) {
                    topics[topic].push(conversation);
                    categorized = true;
                    break;
                }
            }
            
            if (!categorized) {
                topics['general'].push(conversation);
            }
        });
        
        return topics;
    }
    
    async generateOutputFiles(organizedContent, options) {
        const { outputDir = 'cleaned_chat_history' } = options;
        
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        
        for (const [topic, conversations] of Object.entries(organizedContent)) {
            if (conversations.length === 0) continue;
            
            const filename = path.join(outputDir, `${topic}.md`);
            const content = this.generateMarkdownContent(topic, conversations);
            
            fs.writeFileSync(filename, content, 'utf8');
            console.log(`Generated: ${filename} (${conversations.length} conversations)`);
        }
        
        const summaryContent = this.generateSummaryContent(organizedContent);
        const summaryFile = path.join(outputDir, 'SUMMARY.md');
        fs.writeFileSync(summaryFile, summaryContent, 'utf8');
        console.log(`Generated: ${summaryFile}`);
        
        const codeContent = this.extractCodeSnippets(organizedContent);
        const codeFile = path.join(outputDir, 'CODE_SNIPPETS.md');
        fs.writeFileSync(codeFile, codeContent, 'utf8');
        console.log(`Generated: ${codeFile}`);
    }
    
    generateMarkdownContent(topic, conversations) {
        let content = `# ${topic.toUpperCase()} Conversations\n\n`;
        content += `Total conversations: ${conversations.length}\n\n---\n\n`;
        
        conversations.forEach((conversation, index) => {
            content += `## Conversation ${index + 1}\n\n`;
            content += `**Topic:** ${conversation.summary.topic}\n\n`;
            content += `**Keywords:** ${conversation.summary.keywords.join(', ')}\n\n`;
            content += `**Entries:** ${conversation.summary.entryCount}\n\n`;
            
            if (conversation.summary.hasCode) {
                content += `**Contains Code:** Yes\n\n`;
            }
            
            content += `### Content\n\n`;
            
            conversation.entries.forEach((entry, entryIndex) => {
                content += `**Entry ${entryIndex + 1}** (${entry.metadata.timestamp})\n\n`;
                content += `${entry.content}\n\n---\n\n`;
            });
            
            content += `\n\n`;
        });
        
        return content;
    }
    
    generateSummaryContent(organizedContent) {
        let content = `# Chat History Summary\n\n`;
        content += `Generated on: ${new Date().toISOString()}\n\n`;
        
        let totalConversations = 0;
        for (const [topic, conversations] of Object.entries(organizedContent)) {
            totalConversations += conversations.length;
        }
        
        content += `Total conversations: ${totalConversations}\n\n## Breakdown by Topic\n\n`;
        
        for (const [topic, conversations] of Object.entries(organizedContent)) {
            if (conversations.length === 0) continue;
            
            content += `### ${topic.toUpperCase()}\n`;
            content += `- Conversations: ${conversations.length}\n`;
            
            const allKeywords = new Set();
            let codeCount = 0;
            
            conversations.forEach(conv => {
                conv.summary.keywords.forEach(kw => allKeywords.add(kw));
                if (conv.summary.hasCode) codeCount++;
            });
            
            content += `- Code conversations: ${codeCount}\n`;
            content += `- Top keywords: ${Array.from(allKeywords).slice(0, 5).join(', ')}\n\n`;
        }
        
        return content;
    }
    
    extractCodeSnippets(organizedContent) {
        let content = `# Code Snippets from Chat History\n\n`;
        content += `Generated on: ${new Date().toISOString()}\n\n`;
        
        const allSnippets = [];
        
        for (const [topic, conversations] of Object.entries(organizedContent)) {
            conversations.forEach((conversation, convIndex) => {
                conversation.entries.forEach((entry, entryIndex) => {
                    const codeMatches = entry.content.match(/```[\w]*\n([\s\S]*?)\n```/g);
                    
                    if (codeMatches) {
                        codeMatches.forEach((match, snippetIndex) => {
                            const code = match.replace(/```[\w]*\n/, '').replace(/\n```$/, '');
                            const language = match.match(/```(\w+)/)?.[1] || 'text';
                            
                            allSnippets.push({
                                topic,
                                conversation: convIndex + 1,
                                entry: entryIndex + 1,
                                snippet: snippetIndex + 1,
                                language,
                                code,
                                timestamp: entry.metadata.timestamp
                            });
                        });
                    }
                });
            });
        }
        
        const snippetsByLanguage = {};
        allSnippets.forEach(snippet => {
            if (!snippetsByLanguage[snippet.language]) {
                snippetsByLanguage[snippet.language] = [];
            }
            snippetsByLanguage[snippet.language].push(snippet);
        });
        
        for (const [language, snippets] of Object.entries(snippetsByLanguage)) {
            content += `## ${language.toUpperCase()} Snippets (${snippets.length})\n\n`;
            
            snippets.forEach((snippet, index) => {
                content += `### Snippet ${index + 1}\n\n`;
                content += `**Source:** ${snippet.topic} - Conversation ${snippet.conversation}, Entry ${snippet.entry}\n\n`;
                content += `**Timestamp:** ${snippet.timestamp}\n\n`;
                content += `\`\`\`${snippet.language}\n${snippet.code}\n\`\`\`\n\n---\n\n`;
            });
        }
        
        return content;
    }
}

function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Usage: node clean_history.js <input-file> [options]');
        console.log('');
        console.log('Options:');
        console.log('  --output-dir <dir>     Output directory (default: cleaned_chat_history)');
        console.log('  --keywords <words>     Additional keywords to filter by');
        console.log('  --min-length <num>     Minimum content length (default: 10)');
        console.log('  --preserve-code        Preserve code blocks in output');
        console.log('  --remove-markdown      Remove markdown formatting');
        console.log('  --help                 Show this help message');
        process.exit(1);
    }
    
    const inputFile = args[0];
    
    if (!fs.existsSync(inputFile)) {
        console.error(`Input file not found: ${inputFile}`);
        process.exit(1);
    }
    
    const options = {
        outputDir: 'cleaned_chat_history',
        keywords: [],
        minLength: 10,
        preserveCode: true,
        removeMarkdown: true
    };
    
    for (let i = 1; i < args.length; i++) {
        switch (args[i]) {
            case '--output-dir':
                options.outputDir = args[++i];
                break;
            case '--keywords':
                options.keywords = args[++i].split(',').map(k => k.trim());
                break;
            case '--min-length':
                options.minLength = parseInt(args[++i]);
                break;
            case '--preserve-code':
                options.preserveCode = true;
                break;
            case '--remove-markdown':
                options.removeMarkdown = true;
                break;
            case '--help':
                console.log('Usage: node clean_history.js <input-file> [options]');
                process.exit(0);
            default:
                console.error(`Unknown option: ${args[i]}`);
                process.exit(1);
        }
    }
    
    const cleaner = new ChatHistoryCleaner();
    cleaner.processChatHistory(inputFile, options);
}

if (require.main === module) {
    main();
}

module.exports = ChatHistoryCleaner; 