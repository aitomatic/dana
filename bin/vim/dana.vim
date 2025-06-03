" Vim syntax file for Dana Language
" Language: Dana (Domain-Aware NeuroSymbolic Architecture)
" Maintainer: OpenDXA Team
" Copyright: Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
" Latest Revision: 2024

if exists("b:current_syntax")
  finish
endif

" Dana Keywords (from dana_grammar.lark)
syn keyword danaKeyword if elif else while for in def try except finally
syn keyword danaKeyword return break continue pass import from as raise assert
syn keyword danaKeyword and or not is

" Scope prefixes
syn keyword danaScope private public local system

" Boolean and None literals (case-insensitive support)
syn keyword danaBool True true TRUE False false FALSE
syn keyword danaNone None none NONE null NULL

" Built-in types (from grammar)
syn keyword danaType int float str bool list dict tuple set any

" Python built-ins supported in Dana
syn keyword danaBuiltin len sum max min abs round sorted reversed enumerate
syn keyword danaBuiltin all any range type

" Scope markers with colon notation
syn match danaScopeMarker '\<\(private\|public\|local\|system\):'

" String literals (including f-strings and raw strings)
syn region danaString start='"' end='"' contains=danaStringEscape
syn region danaString start="'" end="'" contains=danaStringEscape
syn region danaMultiString start='"""' end='"""' contains=danaStringEscape
syn region danaMultiString start="'''" end="'''" contains=danaStringEscape
syn region danaFString start=/[fF]"/ end=/"/ contains=danaStringEscape,danaFStringExpr
syn region danaFString start=/[fF]'/ end=/'/ contains=danaStringEscape,danaFStringExpr
syn region danaFString start=/[fF]"""/ end=/"""/ contains=danaStringEscape,danaFStringExpr
syn region danaFString start=/[fF]'''/ end=/'''/ contains=danaStringEscape,danaFStringExpr
syn region danaRawString start=/[rR]"/ end=/"/
syn region danaRawString start=/[rR]'/ end=/'/
syn region danaRawString start=/[rR]"""/ end=/"""/
syn region danaRawString start=/[rR]'''/ end=/'''/
syn match danaStringEscape '\\.' contained
syn region danaFStringExpr start='{' end='}' contained contains=danaNumber,danaFloat,danaIdentifier

" Numbers
syn match danaNumber '\<\d\+\>'
syn match danaFloat '\<\d\+\.\d\+\>'
syn match danaFloat '\<\d\+[eE][+-]\?\d\+\>'
syn match danaFloat '\<\d\+\.\d\+[eE][+-]\?\d\+\>'

" Comments
syn match danaComment '#.*$'

" Functions and identifiers
syn match danaFunction '\<[a-zA-Z_][a-zA-Z0-9_]*\s*('me=e-1
syn match danaIdentifier '\<[a-zA-Z_][a-zA-Z0-9_]*\>'

" Operators (from grammar)
syn match danaOperator '[+\-*/%<>=!]'
syn match danaOperator '\*\*'   " Power operator
syn match danaOperator '//'     " Floor division
syn match danaOperator '=='     " Equality
syn match danaOperator '!='     " Not equal
syn match danaOperator '>='     " Greater or equal
syn match danaOperator '<='     " Less or equal
syn match danaOperator '|'      " Pipe operator

" Delimiters
syn match danaDelimiter '[(){}[\],;:]'

" Define the default highlighting
hi def link danaKeyword Keyword
hi def link danaScope Special
hi def link danaScopeMarker Special
hi def link danaType Type
hi def link danaBuiltin Function
hi def link danaBool Boolean
hi def link danaNone Constant
hi def link danaString String
hi def link danaMultiString String
hi def link danaFString String
hi def link danaRawString String
hi def link danaStringEscape SpecialChar
hi def link danaFStringExpr SpecialChar
hi def link danaNumber Number
hi def link danaFloat Float
hi def link danaComment Comment
hi def link danaFunction Function
hi def link danaIdentifier Identifier
hi def link danaOperator Operator
hi def link danaDelimiter Delimiter

" Set filetype
let b:current_syntax = "dana"

" Indentation settings
setlocal autoindent
setlocal smartindent
setlocal expandtab
setlocal tabstop=4
setlocal shiftwidth=4
setlocal softtabstop=4

" Folding
setlocal foldmethod=indent
setlocal foldlevelstart=99

" File type detection
augroup dana
  autocmd!
  autocmd BufRead,BufNewFile *.na setfiletype dana
augroup END

" Key mappings for Dana development
nnoremap <F5> :!bin/dana %<CR>
nnoremap <leader>dr :!bin/dana %<CR>
nnoremap <leader>dc :!bin/dana --check %<CR>

" Abbreviations for common Dana patterns
iabbrev pub: public:
iabbrev priv: private:
iabbrev loc: local:
iabbrev sys: system: 