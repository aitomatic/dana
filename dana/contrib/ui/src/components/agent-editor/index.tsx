import { Editor, useMonaco } from "@monaco-editor/react";
import { useCallback, useEffect, useMemo } from "react";
import type { editor } from "monaco-editor";
import { IconAlertTriangle, IconX } from "@tabler/icons-react";

// Define the correct theme type to match Monaco's requirements
type BuiltinTheme = "vs" | "vs-dark" | "hc-black" | "hc-light";

// Theme data interface to satisfy TypeScript
interface MonacoTheme {
  base: BuiltinTheme;
  inherit: boolean;
  rules: Array<{
    token: string;
    foreground: string;
    fontStyle?: string;
    background?: string;
  }>;
  colors: Record<string, string>;
}

// Validation interface
interface ValidationResult {
  hasQuery: boolean;
  hasResponse: boolean;
  isValid: boolean;
  queryValue?: string;
  responseValue?: string;
}

/**
 * AgentEditor Component
 *
 * A Monaco-based code editor specifically designed for agent configuration with validation.
 *
 * Features:
 * - Syntax highlighting for .na language
 * - @ mention support for agents, MCP clients, and resources
 * - Validation for required query and response fields
 * - Visual indicators for validation status
 * - Theme-aware styling (light/dark mode)
 * - Save functionality with Ctrl+S / Cmd+S shortcut
 *
 * @example
 * ```tsx
 * // Basic usage with validation
 * <AgentEditor
 *   value={agentCode}
 *   onChange={setAgentCode}
 *   placeholder="Enter your agent code here..."
 * />
 *
 * // Usage without validation
 * <AgentEditor
 *   value={agentCode}
 *   onChange={setAgentCode}
 *   enableValidation={false}
 * />
 *
 * // Usage with validation callback
 * <AgentEditor
 *   value={agentCode}
 *   onChange={setAgentCode}
 *   onValidationChange={(validation) => {
 *     console.log('Validation state:', validation);
 *     // validation.isValid - boolean
 *     // validation.hasQuery - boolean
 *     // validation.hasResponse - boolean
 *     // validation.queryValue - string | undefined
 *     // validation.responseValue - string | undefined
 *   }}
 * />
 *
 * // Usage with save functionality
 * <AgentEditor
 *   value={agentCode}
 *   onChange={setAgentCode}
 *   onSave={() => {
 *     console.log('Saving agent code...');
 *     // Trigger save logic here
 *     saveAgentCode(agentCode);
 *   }}
 * />
 *
 * // Example valid content:
 * // query = "What is the weather today?"
 * // response = "I'll check the weather for you."
 * ```
 */
export const AgentEditor = ({
  value,
  onChange,
  placeholder,
  enableValidation = true,
  onValidationChange,
  onSave,
  readOnly = false,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  enableValidation?: boolean;
  onValidationChange?: (validation: ValidationResult) => void;
  onSave?: () => void;
  readOnly?: boolean;
}) => {
  const monaco = useMonaco();
  const isDark = false;

  // Validation function
  const validateContent = useCallback(
    (content: string): ValidationResult => {
      if (!enableValidation) {
        return { hasQuery: true, hasResponse: true, isValid: true };
      }

      const lines = content.split("\n");
      let hasQuery = false;
      let hasResponse = false;
      let queryValue = "";
      let responseValue = "";

      for (const line of lines) {
        const trimmedLine = line.trim();

        // Skip empty lines and comments
        if (!trimmedLine || trimmedLine.startsWith("#")) {
          continue;
        }

        // Check for query assignment (various formats)
        if (
          trimmedLine.startsWith("query =") ||
          trimmedLine.startsWith("query=")
        ) {
          hasQuery = true;
          // Extract value, handling different quote styles and empty values
          const valueMatch = trimmedLine.match(/^query\s*=\s*(.+)$/);
          if (valueMatch) {
            queryValue = valueMatch[1].trim();
            // Remove quotes if present
            queryValue = queryValue.replace(/^["']|["']$/g, "");
          }
        }

        // Check for response assignment (various formats)
        if (
          trimmedLine.startsWith("response =") ||
          trimmedLine.startsWith("response=")
        ) {
          hasResponse = true;
          // Extract value, handling different quote styles and empty values
          const valueMatch = trimmedLine.match(/^response\s*=\s*(.+)$/);
          if (valueMatch) {
            responseValue = valueMatch[1].trim();
            // Remove quotes if present
            responseValue = responseValue.replace(/^["']|["']$/g, "");
          }
        }
      }

      // Check if values are not empty
      const hasValidQuery = hasQuery && queryValue.length > 0;
      const hasValidResponse = hasResponse && responseValue.length > 0;

      return {
        hasQuery: hasValidQuery,
        hasResponse: hasValidResponse,
        isValid: hasValidQuery && hasValidResponse,
        queryValue: hasValidQuery ? queryValue : undefined,
        responseValue: hasValidResponse ? responseValue : undefined,
      };
    },
    [enableValidation],
  );

  // Validation state
  const validation = useMemo(
    () => validateContent(value),
    [value, validateContent],
  );

  // Notify parent of validation changes
  useEffect(() => {
    if (onValidationChange) {
      onValidationChange(validation);
    }
  }, [validation, onValidationChange]);

  // Theme definitions moved to useEffect for better organization
  useEffect(() => {
    if (!monaco) return;

    // Professional light theme
    const professionalLight: MonacoTheme = {
      base: "vs",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "0969da", fontStyle: "bold" },
        { token: "string", foreground: "0550ae" },
        { token: "comment", foreground: "6e7781", fontStyle: "italic" },
        { token: "number", foreground: "0969da" },
        { token: "operator", foreground: "cf222e" },
        { token: "identifier", foreground: "24292f" },
        { token: "variable", foreground: "953800" },
        { token: "variable.private", foreground: "8250df", fontStyle: "bold" },
        {
          token: "variable.private.name",
          foreground: "cf222e",
          fontStyle: "bold",
        },
        {
          token: "variable.interpolation",
          foreground: "953800",
          background: "f6f8fa",
        },
        { token: "mention-agent", foreground: "8250df", fontStyle: "bold" },
        { token: "mention-mcp", foreground: "1f883d", fontStyle: "bold" },
        { token: "mention-resource", foreground: "cf222e", fontStyle: "bold" },
        {
          token: "mention",
          foreground: "0969da",
          background: "ddf4ff",
          fontStyle: "bold",
        },
        { token: "function", foreground: "8250df" },
        { token: "function.special", foreground: "1f883d", fontStyle: "bold" },
        { token: "function.log", foreground: "1f883d", fontStyle: "bold" },
        { token: "method", foreground: "8250df" },
        { token: "property", foreground: "953800" },
        { token: "string.escape", foreground: "0969da" },
      ],
      colors: {
        "editor.background": "#ffffff",
        "editor.foreground": "#24292f",
        "editor.lineHighlightBackground": "#f6f8fa",
        "editor.selectionBackground": "#0969da26",
        "editor.inactiveSelectionBackground": "#0969da1a",
        "editorLineNumber.foreground": "#8c959f",
        "editorLineNumber.activeForeground": "#24292f",
        "editorCursor.foreground": "#24292f",
        "editorWhitespace.foreground": "#afb8c133",
        "editorIndentGuide.background": "#d1d9e0b3",
        "editorIndentGuide.activeBackground": "#8c959f",
        "editorBracketMatch.background": "#0969da26",
        "editorBracketMatch.border": "#0969da",
      },
    };

    // Professional dark theme
    const professionalDark: MonacoTheme = {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "79c0ff", fontStyle: "bold" },
        { token: "string", foreground: "a5d6ff" },
        { token: "comment", foreground: "8b949e", fontStyle: "italic" },
        { token: "number", foreground: "79c0ff" },
        { token: "operator", foreground: "ff7b72" },
        { token: "identifier", foreground: "f0f6fc" },
        { token: "variable", foreground: "ffa657" },
        { token: "variable.private", foreground: "d2a8ff", fontStyle: "bold" },
        {
          token: "variable.private.name",
          foreground: "ff7b72",
          fontStyle: "bold",
        },
        {
          token: "variable.interpolation",
          foreground: "ffa657",
          background: "21262d",
        },
        { token: "mention-agent", foreground: "d2a8ff", fontStyle: "bold" },
        { token: "mention-mcp", foreground: "7ee787", fontStyle: "bold" },
        { token: "mention-resource", foreground: "ff7b72", fontStyle: "bold" },
        {
          token: "mention",
          foreground: "79c0ff",
          background: "1c2128",
          fontStyle: "bold",
        },
        { token: "function", foreground: "d2a8ff" },
        { token: "function.special", foreground: "7ee787", fontStyle: "bold" },
        { token: "function.log", foreground: "7ee787", fontStyle: "bold" },
        { token: "method", foreground: "d2a8ff" },
        { token: "property", foreground: "ffa657" },
        { token: "string.escape", foreground: "79c0ff" },
      ],
      colors: {
        "editor.background": "#0c111d",
        "editor.foreground": "#f0f6fc",
        "editor.lineHighlightBackground": "#21262d",
        "editor.selectionBackground": "#264f78",
        "editor.inactiveSelectionBackground": "#264f7840",
        "editorLineNumber.foreground": "#6e7681",
        "editorLineNumber.activeForeground": "#f0f6fc",
        "editorCursor.foreground": "#f0f6fc",
        "editorWhitespace.foreground": "#484f58",
        "editorIndentGuide.background": "#30363d",
        "editorIndentGuide.activeBackground": "#6e7681",
        "editorBracketMatch.background": "#264f7840",
        "editorBracketMatch.border": "#79c0ff",
      },
    };

    // Define themes with correct typing
    monaco.editor.defineTheme("professional-light", professionalLight);
    monaco.editor.defineTheme("professional-dark", professionalDark);

    // Set the appropriate theme
    monaco.editor.setTheme(isDark ? "professional-dark" : "professional-light");

    // Add CSS for mention boxes with theme-aware colors
    const existingStyle = document.getElementById("agent-editor-styles");
    if (existingStyle) {
      existingStyle.remove();
    }

    const style = document.createElement("style");
    style.id = "agent-editor-styles";
    style.textContent = `
      .mention-agent-box {
        color: ${isDark ? "#d2a8ff" : "#8250df"} !important;
        border-radius: 3px !important;
        padding: 1px 4px !important;
        font-weight: bold !important;
        border: 1px solid ${isDark ? "#d2a8ff" : "#6f42c1"} !important;
        display: inline !important;
        line-height: normal !important;
        vertical-align: baseline !important;
        margin: 0 !important;
        box-decoration-break: clone !important;
      }
      .mention-mcp-box {
        color: ${isDark ? "#7ee787" : "#1f883d"} !important;
        border-radius: 3px !important;
        padding: 1px 4px !important;
        font-weight: bold !important;
        border: 1px solid ${isDark ? "#7ee787" : "#1a7f37"} !important;
        display: inline !important;
        line-height: normal !important;
        vertical-align: baseline !important;
        margin: 0 !important;
        box-decoration-break: clone !important;
      }
      .mention-resource-box {
        color: ${isDark ? "#ff7b72" : "#cf222e"} !important;
        border-radius: 3px !important;
        padding: 1px 4px !important;
        font-weight: bold !important;
        border: 1px solid ${isDark ? "#ff7b72" : "#a40e26"} !important;
        display: inline !important;
        line-height: normal !important;
        vertical-align: baseline !important;
        margin: 0 !important;
        box-decoration-break: clone !important;
      }
    `;
    document.head.appendChild(style);
  }, [monaco, isDark]);

  const handleEditorDidMount = useCallback(
    (editor: any, monaco: any) => {
      // Skip interactive features if readOnly
      if (readOnly) {
        // Set enhanced editor options for read-only mode
        editor.updateOptions({
          fontSize: 14,
          lineHeight: 20,
          fontFamily:
            '"Fira Code", "SF Mono", Monaco, Inconsolata, "Roboto Mono", Consolas, "Courier New", monospace',
          lineNumbers: "on",
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          wordWrap: "on",
          wordWrapColumn: 120,
          wordWrapBreakAfterCharacters: "all",
          wordWrapBreakBeforeCharacters: "all",
          renderLineHighlight: "line",
          renderWhitespace: "selection",
          bracketPairColorization: { enabled: true },
          guides: {
            indentation: true,
            bracketPairs: true,
          },
          smoothScrolling: true,
          cursorSmoothCaretAnimation: "on",
          padding: { top: 16, bottom: 16 },
          readOnly: true,
        });
        return;
      }

      // Register the .na language
      monaco.languages.register({ id: "na" });

      // Define sample resources for @ mentions
      const sampleAgents = ["agent 1", "agent 2"];
      const sampleMcpClients = ["mcp client 1", "mcp client 2"];
      const sampleResources = [
        "resource 1",
        "resource 2",
        "resource 3",
        "resource 4",
        "resource 5",
        "resource 6",
        "resource 7",
        "resource 8",
        "resource 9",
      ];

      // Function to create mention decorations
      const createMentionDecorations = () => {
        const model = editor.getModel();
        if (!model) return;

        const decorations: any[] = [];
        const text = model.getValue();

        // Single regex to find all bracketed mentions
        const mentionRegex = /\[@(agent|mcp|resource):[^\]]+\]/g;
        let match;

        while ((match = mentionRegex.exec(text)) !== null) {
          const startPos = model.getPositionAt(match.index);
          const endPos = model.getPositionAt(match.index + match[0].length);

          // Determine className based on mention type
          let className = "mention-box";
          if (match[1] === "agent") {
            className = "mention-agent-box";
          } else if (match[1] === "mcp") {
            className = "mention-mcp-box";
          } else if (match[1] === "resource") {
            className = "mention-resource-box";
          }

          decorations.push({
            range: new monaco.Range(
              startPos.lineNumber,
              startPos.column,
              endPos.lineNumber,
              endPos.column,
            ),
            options: {
              className: className,
              stickiness:
                monaco.editor.TrackedRangeStickiness
                  .NeverGrowsWhenTypingAtEdges,
            },
          });
        }

        // Apply decorations
        editor.deltaDecorations([], decorations);
      };

      // Function to prevent editing of mention ranges
      const preventMentionEditing = () => {
        // Store current mention ranges
        let mentionRanges: any[] = [];

        const updateMentionRanges = () => {
          const model = editor.getModel();
          if (!model) return;

          mentionRanges = [];
          const text = model.getValue();
          const mentionRegex = /\[@(?:agent|mcp|resource):[^\]]+\]/g;
          let match;

          while ((match = mentionRegex.exec(text)) !== null) {
            const startPos = model.getPositionAt(match.index);
            const endPos = model.getPositionAt(match.index + match[0].length);
            mentionRanges.push({
              startLine: startPos.lineNumber,
              startColumn: startPos.column,
              endLine: endPos.lineNumber,
              endColumn: endPos.column,
              range: new monaco.Range(
                startPos.lineNumber,
                startPos.column,
                endPos.lineNumber,
                endPos.column,
              ),
            });
          }
        };

        // Override typing behavior
        editor.addCommand(monaco.KeyMod.chord(monaco.KeyCode.Backspace), () => {
          const position = editor.getPosition();
          if (!position) return;

          // Check if we're trying to delete part of a mention
          for (const mention of mentionRanges) {
            if (
              position.lineNumber === mention.startLine &&
              position.column > mention.startColumn &&
              position.column <= mention.endColumn
            ) {
              // Delete the entire mention instead
              editor.executeEdits("", [
                {
                  range: mention.range,
                  text: "",
                },
              ]);
              return;
            }
          }

          // Normal backspace - trigger the default behavior
          editor.trigger("keyboard", "deleteLeft");
        });

        // Override delete key
        editor.addCommand(monaco.KeyMod.chord(monaco.KeyCode.Delete), () => {
          const position = editor.getPosition();
          if (!position) return;

          // Check if we're trying to delete part of a mention
          for (const mention of mentionRanges) {
            if (
              position.lineNumber === mention.startLine &&
              position.column >= mention.startColumn &&
              position.column < mention.endColumn
            ) {
              // Delete the entire mention instead
              editor.executeEdits("", [
                {
                  range: mention.range,
                  text: "",
                },
              ]);
              return;
            }
          }

          // Normal delete - trigger the default behavior
          editor.trigger("keyboard", "deleteRight");
        });

        // Block typing inside mentions
        editor.onWillType((_: string) => {
          const position = editor.getPosition();
          if (!position) return;

          // Check if typing inside a mention
          for (const mention of mentionRanges) {
            if (
              position.lineNumber === mention.startLine &&
              position.column > mention.startColumn &&
              position.column < mention.endColumn
            ) {
              // Block the typing
              return;
            }
          }
        });

        // Update ranges when content changes
        editor.onDidChangeModelContent(() => {
          setTimeout(() => {
            updateMentionRanges();
            createMentionDecorations();
          }, 0);
        });

        // Prevent cursor placement inside mentions
        editor.onDidChangeCursorPosition((e: any) => {
          const position = e.position;

          for (const mention of mentionRanges) {
            if (
              position.lineNumber === mention.startLine &&
              position.column > mention.startColumn &&
              position.column < mention.endColumn
            ) {
              // Move cursor to end of mention
              editor.setPosition({
                lineNumber: mention.endLine,
                column: mention.endColumn,
              });
              break;
            }
          }
        });

        // Initial setup
        updateMentionRanges();

        // Register completion provider for @ mentions
        monaco.languages.registerCompletionItemProvider("na", {
          triggerCharacters: ["@"],
          provideCompletionItems: (model: any, position: any) => {
            const word = model.getWordUntilPosition(position);
            const range = {
              startLineNumber: position.lineNumber,
              endLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endColumn: word.endColumn,
            };

            const lineContent = model.getLineContent(position.lineNumber);
            const beforeCursor = lineContent.substring(0, position.column - 1);

            // Check for @ mention completions
            if (beforeCursor.endsWith("@") || /@\w*$/.test(beforeCursor)) {
              const suggestions: any[] = [];

              // Add agent suggestions
              sampleAgents.forEach((agent) => {
                suggestions.push({
                  label: `@agent: ${agent}`,
                  kind: monaco.languages.CompletionItemKind.User,
                  insertText: `[agent: ${agent}]`,
                  documentation: `AI Agent: ${agent}`,
                  range: range,
                  detail: "AI Agent",
                });
              });

              // Add MCP client suggestions
              sampleMcpClients.forEach((mcp) => {
                suggestions.push({
                  label: `@mcp: ${mcp}`,
                  kind: monaco.languages.CompletionItemKind.Module,
                  insertText: `[mcp: ${mcp}]`,
                  documentation: `MCP Client: ${mcp}`,
                  range: range,
                  detail: "MCP Client",
                });
              });

              // Add resource suggestions
              sampleResources.forEach((resource) => {
                suggestions.push({
                  label: `@resource: ${resource}`,
                  kind: monaco.languages.CompletionItemKind.Reference,
                  insertText: `[resource: ${resource}]`,
                  documentation: `Resource: ${resource}`,
                  range: range,
                  detail: "Resource",
                });
              });

              return { suggestions };
            }

            return { suggestions: [] };
          },
        });

        // Register save command (Ctrl+S / Cmd+S)
        if (onSave) {
          editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            // Prevent default browser save behavior
            event?.preventDefault();
            onSave();
          });
        }
      };

      // Enhanced language configuration with more token types
      monaco.languages.setMonarchTokensProvider("na", {
        keywords: [
          "with",
          "as",
          "private",
          "log",
          "while",
          "True",
          "False",
          "None",
          "break",
          "continue",
          "if",
          "elif",
          "else",
          "for",
          "in",
          "return",
          "input",
          "print",
          "def",
          "class",
          "import",
          "from",
          "try",
          "except",
          "finally",
          "raise",
          "and",
          "or",
          "not",
          "knowledge",
          "resources",
          "format",
        ],

        tokenizer: {
          root: [
            // Knowledge blocks
            [
              /\bwith\s+knowledge\s*\(/,
              { token: "keyword", next: "@knowledge_block" },
            ],

            // @ mentions for resources
            [/@[a-zA-Z_]\w*:?/, "mention"],

            // Private variables (private.variable_name)
            [/\bprivate\.[a-zA-Z_]\w*/, "variable.private.name"],

            // Log statements (log.info, log.debug, etc.)
            [/\blog\.(info|debug|warning|error|critical)/, "function.log"],

            // Special .na functions
            [/\b(call_resources|reason|plan)\s*(?=\()/, "function.special"],

            // Regular keywords
            [
              /\b(?:with|as|private|log|while|True|False|None|break|continue|if|elif|else|for|in|return|input|print|def|class|import|from|try|except|finally|raise|and|or|not)\b/,
              "keyword",
            ],

            // Function definitions and calls
            [/\b[a-zA-Z_]\w*(?=\s*\()/, "function"],

            // Method calls
            [/\.[a-zA-Z_]\w*(?=\s*\()/, "method"],

            // Properties and attributes
            [/\.[a-zA-Z_]\w*/, "property"],

            // Variables (after = sign)
            [/[a-zA-Z_]\w*(?=\s*=)/, "variable"],

            // F-strings with variable interpolation
            [/f"/, { token: "string", next: "@fstring_double" }],
            [/f'/, { token: "string", next: "@fstring_single" }],

            // Regular strings
            [/"/, { token: "string", next: "@string_double" }],
            [/'/, { token: "string", next: "@string_single" }],

            // Triple quoted strings
            [/"""/, { token: "string", next: "@string_triple_double" }],
            [/'''/, { token: "string", next: "@string_triple_single" }],

            // Comments
            [/#.*$/, "comment"],

            // Numbers
            [/\b\d+\.?\d*\b/, "number"],

            // Operators
            [/[+\-*/=<>!&|%^~]/, "operator"],

            // Brackets
            [/[(){}\[\]]/, "delimiter.bracket"],

            // Identifiers
            [/[a-zA-Z_]\w*/, "identifier"],

            // Whitespace
            [/\s+/, "white"],
          ],

          // Knowledge block state
          knowledge_block: [
            [/"[^"]*"/, "string"],
            [/'[^']*'/, "string"],
            [/\)/, { token: "delimiter.bracket", next: "@pop" }],
            [/[^)"']+/, "white"],
          ],

          // F-string states with variable interpolation
          fstring_double: [
            [/\{[^}]*\}/, "variable.interpolation"],
            [/[^"\\{]+/, "string"],
            [/\\./, "string.escape"],
            [/"/, { token: "string", next: "@pop" }],
          ],

          fstring_single: [
            [/\{[^}]*\}/, "variable.interpolation"],
            [/[^'\\{]+/, "string"],
            [/\\./, "string.escape"],
            [/'/, { token: "string", next: "@pop" }],
          ],

          // Regular string states
          string_double: [
            [/[^"\\]+/, "string"],
            [/\\./, "string.escape"],
            [/"/, { token: "string", next: "@pop" }],
          ],

          string_single: [
            [/[^'\\]+/, "string"],
            [/\\./, "string.escape"],
            [/'/, { token: "string", next: "@pop" }],
          ],

          string_triple_double: [
            [/[^"\\]+/, "string"],
            [/\\./, "string.escape"],
            [/"""/, { token: "string", next: "@pop" }],
            [/"/, "string"],
          ],

          string_triple_single: [
            [/[^'\\]+/, "string"],
            [/\\./, "string.escape"],
            [/'''/, { token: "string", next: "@pop" }],
            [/'/, "string"],
          ],
        },
      });

      // Set enhanced editor options
      editor.updateOptions({
        fontSize: 14,
        lineHeight: 20,
        fontFamily:
          '"Fira Code", "SF Mono", Monaco, Inconsolata, "Roboto Mono", Consolas, "Courier New", monospace',
        lineNumbers: "on",
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        wordWrap: "on",
        wordWrapColumn: 120,
        wordWrapBreakAfterCharacters: "all",
        wordWrapBreakBeforeCharacters: "all",
        renderLineHighlight: "line",
        renderWhitespace: "selection",
        bracketPairColorization: { enabled: true },
        guides: {
          indentation: true,
          bracketPairs: true,
        },
        smoothScrolling: true,
        cursorSmoothCaretAnimation: "on",
        suggestOnTriggerCharacters: true,
        acceptSuggestionOnCommitCharacter: true,
        tabCompletion: "on",
        padding: { top: 16, bottom: 16 },
      });

      preventMentionEditing();
      createMentionDecorations();
    },
    [readOnly, onSave],
  );

  // Correctly type the editor options
  const editorOptions: editor.IStandaloneEditorConstructionOptions = {
    placeholder: placeholder,
    readOnly: readOnly,
  };

  return (
    <div className="flex overflow-hidden flex-col w-full h-full rounded-lg border border-gray-200 shadow-sm">
      {/* Validation Panel */}
      {enableValidation && !validation.isValid && (
        <div
          className={`px-4 py-3 border-b ${
            isDark
              ? "bg-[#0c111d] border-gray-700 text-white"
              : "bg-gray-50 border-gray-200"
          }`}
        >
          <div className="flex gap-2 items-center mb-2">
            <IconAlertTriangle
              size={16}
              className={isDark ? "text-yellow-400" : "text-yellow-600"}
            />
            <span
              className={`text-sm font-medium ${isDark ? "text-white" : "text-yellow-600"}`}
            >
              Required Fields Missing
            </span>
          </div>
          <div className="space-y-1">
            {!validation.hasQuery && (
              <div className="flex gap-2 items-center">
                <IconX size={14} className="text-red-500" />
                <span
                  className={`text-sm ${isDark ? "text-white" : "text-gray-600"}`}
                >
                  Missing or empty{" "}
                  <code
                    className={`px-1 py-0.5 rounded text-xs ${
                      isDark
                        ? "bg-gray-700 text-gray-200"
                        : "bg-gray-200 text-gray-800"
                    }`}
                  >
                    query = "..."
                  </code>
                </span>
              </div>
            )}
            {!validation.hasResponse && (
              <div className="flex gap-2 items-center">
                <IconX size={14} className="text-red-500" />
                <span
                  className={`text-sm ${isDark ? "text-white" : "text-gray-600"}`}
                >
                  Missing or empty{" "}
                  <code
                    className={`px-1 py-0.5 rounded text-xs ${
                      isDark
                        ? "bg-gray-700 text-gray-200"
                        : "bg-gray-200 text-gray-800"
                    }`}
                  >
                    response = "..."
                  </code>
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          defaultLanguage="na"
          value={value}
          onChange={(value) => onChange(value || "")}
          theme={isDark ? "professional-dark" : "professional-light"}
          onMount={handleEditorDidMount}
          width="100%"
          options={editorOptions}
        />
      </div>
    </div>
  );
};
