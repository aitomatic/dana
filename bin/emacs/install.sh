#!/bin/bash
# Install Dana Language Support for Emacs
# Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
# This script sets up Dana mode, LSP integration, and key bindings

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing Dana Language Support for Emacs...${NC}"

# Check if Emacs is installed
if ! command -v emacs &> /dev/null; then
    echo -e "${RED}❌ Error: Emacs is not installed${NC}"
    echo -e "${YELLOW}💡 Please install Emacs first:${NC}"
    echo "   - macOS: brew install emacs"
    echo "   - Ubuntu: apt install emacs"
    echo "   - Or download from: https://www.gnu.org/software/emacs/"
    exit 1
fi

# Get Emacs config directory
EMACS_DIR="$HOME/.emacs.d"
echo -e "${BLUE}📁 Emacs config directory: ${EMACS_DIR}${NC}"

# Create directory if it doesn't exist
mkdir -p "$EMACS_DIR"

# Check for LSP dependencies
echo -e "${BLUE}🔍 Checking LSP dependencies...${NC}"
LSP_AVAILABLE=false
if python3 -c "import lsprotocol, pygls" 2>/dev/null; then
    LSP_AVAILABLE=true
    echo -e "${GREEN}✅ LSP dependencies available${NC}"
else
    echo -e "${YELLOW}⚠️  LSP dependencies not found. Install with: pip install lsprotocol pygls${NC}"
fi

# Create Dana mode file
echo -e "${BLUE}📝 Creating Dana mode...${NC}"
cat > "$EMACS_DIR/dana-mode.el" << 'EOF'
;;; dana-mode.el --- Major mode for Dana language

;;; Commentary:
;; Major mode for editing Dana (.na) files
;; Provides syntax highlighting, indentation, and LSP integration

;;; Code:

(defvar dana-mode-hook nil)

(defvar dana-mode-map
  (let ((map (make-keymap)))
    (define-key map "\C-j" 'newline-and-indent)
    (define-key map (kbd "<f5>") 'dana-run-file)
    map)
  "Keymap for Dana major mode")

(add-to-list 'auto-mode-alist '("\\.na\\'" . dana-mode))

(defvar dana-font-lock-keywords
  `(
    ;; Keywords
    (,(regexp-opt '("def" "if" "else" "elif" "while" "for" "try" "except" "finally"
                   "return" "break" "continue" "pass" "import" "from" "as"
                   "struct" "agent" "use" "export" "True" "False" "None"
                   "and" "or" "not" "in" "is") 'words) . font-lock-keyword-face)
    
    ;; Scope prefixes
    ("\\(private\\|public\\|local\\|system\\):" . font-lock-type-face)
    
    ;; Built-in functions
    (,(regexp-opt '("log" "print" "reason" "len" "str" "int" "float" "bool"
                   "list" "dict" "tuple" "set" "range" "enumerate" "zip") 'words) . font-lock-builtin-face)
    
    ;; Comments
    ("#.*" . font-lock-comment-face)
    
    ;; Strings
    ("\".*?\"" . font-lock-string-face)
    ("'.*?'" . font-lock-string-face)
    
    ;; F-strings
    ("f\".*?\"" . font-lock-string-face)
    ("f'.*?'" . font-lock-string-face)
    
    ;; Numbers
    ("\\b[0-9]+\\(\\.[0-9]+\\)?\\b" . font-lock-constant-face)
    
    ;; Function definitions
    ("\\<def\\s-+\\(\\sw+\\)" 1 font-lock-function-name-face)
    )
  "Highlighting expressions for Dana mode.")

(defvar dana-mode-syntax-table
  (let ((st (make-syntax-table)))
    (modify-syntax-entry ?_ "w" st)
    (modify-syntax-entry ?# "<" st)
    (modify-syntax-entry ?\n ">" st)
    st)
  "Syntax table for Dana mode")

(defun dana-indent-line ()
  "Indent current line as Dana code."
  (interactive)
  (let ((savep (> (current-column) (current-indentation)))
        (indent (condition-case nil (max (dana-calculate-indentation) 0)
                  (error 0))))
    (if savep
        (save-excursion (indent-line-to indent))
      (indent-line-to indent))))

(defun dana-calculate-indentation ()
  "Return the column to which the current line should be indented."
  (save-excursion
    (beginning-of-line)
    (cond
     ((bobp) 0)
     ((looking-at "^[ \t]*$") (dana-calculate-indentation))
     (t
      (forward-line -1)
      (let ((prev-indent (current-indentation)))
        (cond
         ((looking-at ".*:\\s-*$") (+ prev-indent 4))
         (t prev-indent)))))))

(defun dana-run-file ()
  "Run the current Dana file."
  (interactive)
  (let ((file (buffer-file-name)))
    (if file
        (compile (format "dana %s" (shell-quote-argument file)))
      (message "Buffer is not visiting a file"))))

(define-derived-mode dana-mode fundamental-mode "Dana"
  "Major mode for editing Dana files."
  (setq font-lock-defaults '(dana-font-lock-keywords))
  (setq indent-line-function 'dana-indent-line)
  (setq comment-start "#")
  (setq comment-end "")
  (setq comment-start-skip "#+\\s-*")
  (use-local-map dana-mode-map)
  (set-syntax-table dana-mode-syntax-table)
  (setq mode-name "Dana")
  (run-hooks 'dana-mode-hook))

(provide 'dana-mode)

;;; dana-mode.el ends here
EOF

# Create LSP configuration if available
if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo -e "${BLUE}📝 Creating LSP configuration...${NC}"
    cat > "$EMACS_DIR/dana-lsp.el" << 'EOF'
;;; dana-lsp.el --- LSP configuration for Dana language

;;; Commentary:
;; LSP configuration for Dana language server

;;; Code:

(require 'lsp-mode)

;; Add Dana language server
(add-to-list 'lsp-language-id-configuration '(dana-mode . "dana"))

(lsp-register-client
 (make-lsp-client :new-connection (lsp-stdio-connection "dana-ls")
                  :major-modes '(dana-mode)
                  :server-id 'dana-ls))

;; Enable LSP for Dana files
(add-hook 'dana-mode-hook #'lsp)

;; LSP UI enhancements (optional)
(with-eval-after-load 'lsp-mode
  (setq lsp-enable-snippet nil)  ; Disable snippets if you don't want them
  (setq lsp-prefer-flymake nil)  ; Use flycheck instead of flymake
  )

(provide 'dana-lsp)

;;; dana-lsp.el ends here
EOF
fi

# Update or create init.el
INIT_FILE="$EMACS_DIR/init.el"
echo -e "${BLUE}⚙️  Configuring Emacs...${NC}"

# Create backup if init.el exists
if [[ -f "$INIT_FILE" ]]; then
    cp "$INIT_FILE" "$INIT_FILE.dana-backup"
    echo -e "${BLUE}📋 Created backup: $INIT_FILE.dana-backup${NC}"
fi

# Check if Dana configuration already exists
if [[ -f "$INIT_FILE" ]] && grep -q "Dana Language Support" "$INIT_FILE"; then
    echo -e "${YELLOW}⚠️  Dana configuration already exists in $INIT_FILE${NC}"
    echo -e "${YELLOW}   Skipping init.el modification. Remove manually if needed.${NC}"
else
    # Add Dana configuration
    cat >> "$INIT_FILE" << 'EOF'

;; ===== Dana Language Support =====
;; Auto-installed by bin/emacs/install.sh

;; Load Dana mode
(add-to-list 'load-path "~/.emacs.d")
(require 'dana-mode)

EOF

    if [[ "$LSP_AVAILABLE" == "true" ]]; then
        cat >> "$INIT_FILE" << 'EOF'
;; LSP Mode (install if not present)
(unless (package-installed-p 'lsp-mode)
  (package-refresh-contents)
  (package-install 'lsp-mode))

;; Load Dana LSP configuration
(require 'dana-lsp)

;; Optional: LSP UI enhancements
(unless (package-installed-p 'lsp-ui)
  (package-refresh-contents)
  (package-install 'lsp-ui))
(require 'lsp-ui)

EOF
    fi

    cat >> "$INIT_FILE" << 'EOF'
;; Dana key bindings
(global-set-key (kbd "C-c d r") 'dana-run-file)

;; ===== End Dana Language Support =====
EOF

    echo -e "${GREEN}✅ Added Dana configuration to $INIT_FILE${NC}"
fi

echo -e "${GREEN}🎉 Dana Language Support successfully installed for Emacs!${NC}"
echo ""

if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo -e "${GREEN}✅ LSP Features Enabled:${NC}"
    echo "  - Real-time syntax checking"
    echo "  - Hover documentation"
    echo "  - Go-to-definition"
    echo "  - Auto-completion"
    echo "  - Error diagnostics"
    echo ""
    echo -e "${BLUE}💡 Emacs LSP Requirements:${NC}"
    echo "  - lsp-mode package (auto-installed)"
    echo "  - Optional: lsp-ui for enhanced UI (auto-installed)"
else
    echo -e "${YELLOW}⚠️  Basic Dana support installed (no LSP features)${NC}"
    echo -e "${BLUE}💡 To enable LSP features:${NC}"
    echo "  1. Install dependencies: pip install lsprotocol pygls"
    echo "  2. Re-run this installer"
fi

echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Start Emacs: emacs"
echo "2. Create or open a .na file"
echo "3. Press F5 or C-c d r to run Dana code"
echo ""
echo -e "${BLUE}💡 Dana Features in Emacs:${NC}"
echo "  - F5: Run current Dana file"
echo "  - C-c d r: Run current Dana file"
echo "  - Syntax highlighting for .na files"
echo "  - Smart indentation"
if [[ "$LSP_AVAILABLE" == "true" ]]; then
    echo "  - Real-time error checking"
    echo "  - Hover help on Dana keywords"
    echo "  - Smart auto-completion"
    echo "  - Go-to-definition"
fi 