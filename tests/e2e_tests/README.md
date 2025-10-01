# Playwright E2E Tests

## Setup

```bash
cd dana-internal/tests
npm install
npx playwright install
```

Ensure Dana Studio is running on `http://127.0.0.1:8080/`

## Run Tests

```bash
# Run all tests
npx playwright test

# Run smoke tests only
npx playwright test smoke_test.spec.ts

# Run with visible browser
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Test Results

```bash
npx playwright show-report
```
