# OpenDXA Frontend Services & Stores

## Overview

This directory contains the API services, Zustand stores, and utilities for the OpenDXA frontend.

## Files

### API Services
- `api.ts` - Centralized API service using Axios
- `constants.ts` - Application constants and configuration

### Stores
- `api-store.ts` - API connection and health state
- `poet-store.ts` - POET service state management
- `ui-store.ts` - UI state (dialogs, navigation, notifications)
- `agent-store.ts` - Agent management state
- `topic-store.ts` - Topic management state
- `document-store.ts` - Document management state

### Hooks
- `use-api.ts` - Custom hooks for API operations

### Utilities
- `utils.ts` - Common utility functions

## Usage

```typescript
// API Service
import { apiService } from '@/lib/api';
const health = await apiService.checkHealth();

// Stores
import { useApiStore, usePoetStore, useTopicStore, useDocumentStore } from '@/stores';
const { isHealthy } = useApiStore();
const { configurePoet } = usePoetStore();
const { topics, createTopic } = useTopicStore();
const { documents, uploadDocument } = useDocumentStore();

// Hooks
import { useApiInitialization, useTopicOperations, useDocumentOperations } from '@/hooks/use-api';
useApiInitialization(); // Auto-initialize API
const { topics, createTopic } = useTopicOperations();
const { documents, uploadDocument } = useDocumentOperations();

// Utilities
import { formatApiError, cn } from '@/lib/utils';
```

## Environment

Set `VITE_API_BASE_URL` in `.env.local` (defaults to `http://localhost:12345`)

## Architecture Overview

The frontend follows a clean architecture pattern with:

- **API Services**: Centralized API communication layer
- **Zustand Stores**: State management for different application domains
- **Custom Hooks**: Reusable logic for components
- **Utilities**: Common helper functions

## API Services

### `api.ts`
Centralized API service using Axios for all OpenDXA API communications.

**Features:**
- Automatic request/response logging
- Standardized error handling
- Type-safe API calls
- Interceptors for common operations

**Available Endpoints:**
- `GET /health` - Health check
- `GET /` - Root information
- `POST /poet/configure` - Configure POET
- `GET /poet/domains` - Get available domains

**Usage:**
```typescript
import { apiService } from '@/lib/api';

// Health check
const health = await apiService.checkHealth();

// Configure POET
const config = await apiService.configurePoet({
  domain: 'healthcare',
  retries: 3,
  enable_training: true
});
```

## Zustand Stores

### `api-store.ts`
Manages API connection state, health checks, and general API status.

**State:**
- API health status
- Connection availability
- Loading states
- Error handling

**Usage:**
```typescript
import { useApiStore } from '@/stores/api-store';

const { isHealthy, checkHealth, error } = useApiStore();
```

### `poet-store.ts`
Manages POET service state including configurations and domains.

**State:**
- Current POET configuration
- Available domains
- Selected domain
- Loading states

**Usage:**
```typescript
import { usePoetStore } from '@/stores/poet-store';

const { configurePoet, availableDomains, selectedDomain } = usePoetStore();
```

### `ui-store.ts`
Manages UI state including dialogs, navigation, and notifications.

**State:**
- Dialog visibility
- Navigation state
- Theme preferences
- Notifications

**Usage:**
```typescript
import { useUIStore } from '@/stores/ui-store';

const { 
  openCreateAgentDialog, 
  addNotification, 
  theme 
} = useUIStore();
```

### `agent-store.ts`
Manages agent-related state and operations.

**State:**
- Agent list
- Selected agent
- Dialog states
- Loading states

**Usage:**
```typescript
import { useAgentStore } from '@/stores/agent-store';

const { 
  agents, 
  openCreateAgentDialog, 
  selectedAgent 
} = useAgentStore();
```

## Custom Hooks

### `use-api.ts`
Provides high-level API operations with automatic error handling and notifications.

**Hooks:**
- `useApiInitialization()` - Initialize API connection on app start
- `usePoetOperations()` - POET-specific operations with notifications
- `useApiHealth()` - API health monitoring

**Usage:**
```typescript
import { useApiInitialization, usePoetOperations } from '@/hooks/use-api';

// In your app component
function App() {
  useApiInitialization(); // Auto-initialize API
  return <div>...</div>;
}

// In a component
function PoetConfig() {
  const { configurePoet, availableDomains } = usePoetOperations();
  // ...
}
```

## Utilities

### `utils.ts`
Common utility functions for the application.

**Functions:**
- `cn()` - Class name utility with Tailwind CSS
- `formatApiError()` - Format API errors for display
- `debounce()` / `throttle()` - Performance utilities
- `generateId()` - Generate unique IDs
- `formatDate()` - Date formatting
- `copyToClipboard()` - Clipboard operations

### `constants.ts`
Application constants and configuration values.

**Constants:**
- API configuration
- Endpoint URLs
- UI constants
- Error messages
- Storage keys

## Usage Patterns

### 1. API Operations
```typescript
// Direct API call
const health = await apiService.checkHealth();

// Using store
const { checkHealth, isHealthy } = useApiStore();
await checkHealth();

// Using custom hook
const { configurePoet } = usePoetOperations();
await configurePoet({ domain: 'healthcare' });
```

### 2. State Management
```typescript
// Multiple stores
const { isHealthy } = useApiStore();
const { availableDomains } = usePoetStore();
const { addNotification } = useUIStore();

// Combined operations
if (isHealthy && availableDomains.length > 0) {
  addNotification({
    type: 'success',
    title: 'Ready',
    message: 'System is ready'
  });
}
```

### 3. Error Handling
```typescript
import { formatApiError } from '@/lib/utils';

try {
  await apiService.configurePoet(config);
} catch (error) {
  const message = formatApiError(error);
  addNotification({
    type: 'error',
    title: 'Configuration Failed',
    message
  });
}
```

## Development

### Adding New API Endpoints

1. Add endpoint to `api.ts`:
```typescript
async newEndpoint(data: NewEndpointRequest): Promise<NewEndpointResponse> {
  const response = await this.client.post<NewEndpointResponse>('/new-endpoint', data);
  return response.data;
}
```

2. Add types to `api.ts`:
```typescript
export interface NewEndpointRequest {
  // ...
}

export interface NewEndpointResponse {
  // ...
}
```

3. Add to store if needed:
```typescript
// In appropriate store
newEndpoint: async (data: NewEndpointRequest) => {
  set({ isLoading: true });
  try {
    const response = await apiService.newEndpoint(data);
    set({ data: response, isLoading: false });
  } catch (error) {
    set({ error, isLoading: false });
  }
}
```

### Adding New Stores

1. Create store file: `new-store.ts`
2. Define interface and state
3. Export from `stores/index.ts`
4. Add to hooks if needed

## Testing

All stores and services should be tested with:

- Unit tests for individual functions
- Integration tests for API calls
- Store tests for state management
- Hook tests for component logic

## Best Practices

1. **Type Safety**: Always use TypeScript interfaces for API requests/responses
2. **Error Handling**: Use centralized error handling with user-friendly messages
3. **Loading States**: Provide loading indicators for all async operations
4. **Notifications**: Use the notification system for user feedback
5. **Constants**: Use constants for magic strings and configuration values
6. **Hooks**: Create custom hooks for complex logic and reuse
7. **Stores**: Keep stores focused on specific domains
8. **Utilities**: Extract common functionality into utility functions 