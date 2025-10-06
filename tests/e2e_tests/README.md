# Playwright E2E Tests

## Setup

```bash
cd dana-internal/tests/e2e_tests/
```

Ensure Dana Studio is running on `<http://localhost:4041/`

## Run Tests

```bash
# Run all tests
npx playwright test

# Run smoke tests only
npx playwright test smoke_test.spec.ts

# Run essential test base case with only doc
npx playwright test essential_chat_with_doc_base.spec.ts

# Run essential test doc and knowledge pack
npx playwright test essential_chat_with_doc_and_knowledge_pack.spec.ts

# Run with visible browser
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Smoke Tests

Tests the most basic Q&A of the pre-defined agents.

## Essential Tests

### 1\. Essential Chat with Document Base (`essential_chat_with_doc_base.spec.ts`)

Tests the basic chat functionality with document upload and interaction.

### 2\. Essential Chat with Document and Knowledge Pack (`essential_chat_with_doc_and_knowledge_pack.spec.ts`)

Tests advanced chat functionality including:

- Agent training from existing templates
- Document from library
- Knowledge pack generation

## Test Results

```bash
npx playwright show-report
```
