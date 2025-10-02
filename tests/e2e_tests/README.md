# Playwright E2E Tests

## Setup

```bash
cd dana-internal/tests/e2e_tests/
npm init playwright@latest
```

Ensure Dana Studio is running on `http://127.0.0.1:8080/`

## Run Tests

```bash
# Run all tests
npx playwright test

# Run smoke tests only
npx playwright test smoke_test.spec.ts

# Run essential tests
npx playwright test essential_chat_with_doc_base.spec.ts
npx playwright test essential_chat_with_doc_and_knowledge_pack.spec.ts

# Run with visible browser
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Essential Tests

### 1\. Essential Chat with Document Base (`essential_chat_with_doc_base.spec.ts`)

Tests the basic chat functionality with document upload and interaction.

### 2\. Essential Chat with Document and Knowledge Pack (`essential_chat_with_doc_and_knowledge_pack.spec.ts`)

Tests advanced chat functionality including:

- Agent training from existing templates
- Document library integration
- Knowledge pack configuration

## Test Results

```bash
npx playwright show-report
```
