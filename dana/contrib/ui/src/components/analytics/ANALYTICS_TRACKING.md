# Google Analytics Tracking Implementation

## Overview
This document outlines the comprehensive Google Analytics tracking implementation for the Dana Agent Studio UI.

## Configuration
- **Tracking ID**: `G-66GE7JMVY5`
- **Implementation**: Google Analytics 4 (GA4)
- **Libraries**: 
  - Native gtag.js (in `index.html`)
  - `react-ga4` package for React integration

## Architecture

### Core Files
- **`src/lib/analytics.ts`**: Singleton Analytics class with gtag integration
- **`src/lib/constants.ts`**: Analytics configuration (tracking ID, debug mode)
- **`src/hooks/useAnalytics.ts`**: React hooks for tracking (`useAnalytics`, `useDanaAnalytics`)

### Analytics Hooks

#### `useAnalytics()`
Base hook providing:
- `trackEvent(event: GAEvent)`: Track custom events
- `trackPageView(pageView?: GAPageView)`: Track page views
- `setUserProperties(properties: GAUserProperties)`: Set user properties
- `trackTiming(name, value, category, label)`: Track performance timing
- `isEnabled`: Check if analytics is enabled

#### `useDanaAnalytics()`
Dana-specific tracking hook providing:
- **Agent Management**
  - `trackAgentCreation(agentName, domain?)`
  - `trackAgentEdit(agentId, field)`
  - `trackAgentDeletion(agentId)`
  - `trackAgentImport(prebuiltKey, success)`
  - `trackDocumentAssociation(agentId, documentCount)`

- **Library Operations**
  - `trackFileUpload(fileType, fileSize?)`
  - `trackFileDownload(fileType, fileName)`
  - `trackFolderCreation(folderName)`
  - `trackFileExtraction(fileType, extractionType, success)`
  - `trackPdfView(fileName)`

- **Code & Development**
  - `trackCodeGeneration(agentId, duration)`

- **Chat & Interaction**
  - `trackChatMessage(agentId, messageType)`

- **Navigation**
  - `trackTabNavigation(tabName, context)`

- **System & Errors**
  - `trackApiConnection(status, endpoint?)`
  - `trackError(errorType, errorMessage, context?)`

## Implemented Tracking

### ✅ Page Views
**Location**: Automatic via `useAnalytics` hook in routing
- All route changes are automatically tracked
- Includes page title, location, and path

### ✅ Agent Management Events

#### Agent Creation
**Location**: `stores/agent-store.ts` (line 71-75)
```typescript
analytics.trackEvent({
  action: 'create_agent',
  category: 'agent_management',
  label: newAgent.name,
});
```

#### Agent Name Edit
**Location**: `pages/Agents/tabs/OverviewTab.tsx` (line 40)
```typescript
trackAgentEdit(agent.id.toString(), 'name');
```

#### Agent Deletion
**Location**: `components/delete-agent-dialog.tsx` (line 33)
```typescript
trackAgentDeletion(agentId);
```

#### Tab Navigation
**Location**: `pages/Agents/AgentDetailTabs.tsx` (line 113)
```typescript
trackTabNavigation(tab, 'agent_detail');
```

#### Document Association
**Location**: `pages/Agents/tabs/DocumentsTab.tsx` (line 124)
```typescript
trackDocumentAssociation(agent_id, selectedFileIds.length);
```

### ✅ Library Operations

#### File Upload
**Locations**:
1. `components/file-upload.tsx` (line 93)
2. `pages/Agents/tabs/DocumentsTab.tsx` (line 169)

```typescript
trackFileUpload(fileExtension, file.size);
```

#### File Download
**Location**: `pages/Library/index.tsx` (line 224)
```typescript
trackFileDownload(fileExtension, item.name);
```

#### Folder Creation
**Location**: `pages/Library/index.tsx` (line 239)
```typescript
trackFolderCreation(name);
```

#### File Extraction
**Location**: `stores/extraction-file-store.ts`

**Basic Extraction** (Auto-extraction on upload - lines 218, 252):
```typescript
// Success
analytics.trackEvent({
  action: 'file_extraction_success',
  category: 'library',
  label: `${fileExtension}_basic`,
});

// Failure
analytics.trackEvent({
  action: 'file_extraction_failed',
  category: 'library',
  label: `${fileExtension}_basic`,
});
```

**Deep Extraction** (Manual extraction with AI - lines 597, 627):
```typescript
// Success
analytics.trackEvent({
  action: 'file_extraction_success',
  category: 'library',
  label: `${fileExtension}_deep`,
});

// Failure
analytics.trackEvent({
  action: 'file_extraction_failed',
  category: 'library',
  label: `${fileExtension}_deep`,
});
```

**Labels distinguish between**:
- `pdf_basic` - Auto-extraction on upload
- `pdf_deep` - User-triggered deep extraction with AI
- `png_basic` - Auto-extraction for images
- `png_deep` - Deep extraction for images, etc.

### ✅ Chat & Messaging

#### Chat Messages
**Location**: `pages/Agents/chat/chat-view.tsx` (line 208)
```typescript
trackChatMessage(agentId.toString(), 'user');
```

### ✅ Error Tracking

Comprehensive error tracking implemented across:
- Agent operations (creation, deletion, updates)
- File operations (upload, download, extraction)
- Library operations (folder creation, item deletion)
- Document association

**Example**:
```typescript
trackError('agent_deletion_failed', error.message, agentId);
trackError('document_download_failed', error.message, `doc_${item.id}`);
```

## Event Categories

| Category | Description | Example Actions |
|----------|-------------|-----------------|
| `agent_management` | Agent lifecycle events | create_agent, edit_agent, delete_agent |
| `agent_interaction` | User-agent interactions | chat_message |
| `agent_development` | Development activities | generate_code, timing_complete |
| `library` | Library operations | upload_file, download_file, file_extraction |
| `navigation` | UI navigation | tab_navigation |
| `system` | System-level events | api_connection, error |

## Event Naming Convention

**Format**: `{action}_{object}_{status?}`

Examples:
- `create_agent`
- `delete_agent`
- `file_extraction_success`
- `file_extraction_failed`
- `associate_documents`

## Usage Guidelines

### Adding New Tracking

1. **For new event types**: Add to `useDanaAnalytics()` hook in `src/hooks/useAnalytics.ts`
2. **For one-off events**: Use `trackEvent()` directly from `useAnalytics()`
3. **In components**: Import and use `useDanaAnalytics()`

```typescript
import { useDanaAnalytics } from '@/hooks/useAnalytics';

function MyComponent() {
  const { trackAgentCreation, trackError } = useDanaAnalytics();
  
  const handleCreate = async () => {
    try {
      // ... create logic
      trackAgentCreation(name, domain);
    } catch (error) {
      trackError('agent_creation_failed', error.message, context);
    }
  };
}
```

### Best Practices

1. **Always track errors** alongside success events
2. **Include context** in labels (agent ID, file type, etc.)
3. **Track timing** for long-running operations using `trackTiming()`
4. **Set user properties** early in the app lifecycle
5. **Test in debug mode** (automatically enabled in development)

## Viewing Data

### Google Analytics Dashboard
1. Go to [Google Analytics](https://analytics.google.com)
2. Select property ID: `G-66GE7JMVY5`
3. View:
   - **Real-time** → See live events
   - **Reports** → **Engagement** → Events
   - **Reports** → **Engagement** → Pages and screens

### Key Metrics to Monitor

- **Agent Lifecycle**: Creation → Editing → Usage → Deletion funnel
- **File Operations**: Upload success rate, extraction success rate
- **User Engagement**: Tab navigation patterns, chat frequency
- **Error Rates**: By category and type
- **Feature Adoption**: Tab usage, extraction feature usage

## Debug Mode

In development environment:
- Debug mode is automatically enabled
- Events are logged to console
- View in browser console: `window.dataLayer`

## Coverage Summary

| Feature Area | Coverage | Status |
|--------------|----------|--------|
| Page Views | 100% | ✅ Complete |
| Agent Management | 90% | ✅ Excellent |
| Library Operations | 85% | ✅ Excellent |
| Chat & Messaging | 60% | ⚠️ Partial (user messages only) |
| Code Development | 40% | ⚠️ Defined but not used |
| Error Tracking | 80% | ✅ Excellent |
| Performance Timing | 20% | ⚠️ Defined but rarely used |

**Overall Coverage**: ~75% of critical user actions tracked

## Future Enhancements

### High Priority
1. Track agent response messages (not just user messages)
2. Track code generation completion and success rates
3. Add user property setting (user type, session info)
4. Track search interactions and filter usage

### Medium Priority
1. Track workflow creation and execution
2. Track domain knowledge uploads
3. Add performance timing for slow operations
4. Track feature discovery (first-time actions)

### Low Priority
1. Track keyboard shortcuts usage
2. Track UI theme/preference changes
3. A/B test variant tracking

## Troubleshooting

### Events not showing in GA4
1. Check `GA_CONFIG.ENABLED` is `true` in `constants.ts`
2. Verify tracking ID is correct
3. Check browser console for errors
4. Verify ad blockers are disabled for testing

### Debug events in development
```javascript
// In browser console
console.log(window.dataLayer);
```

## Changelog

### 2025-01-01 - Initial Comprehensive Implementation
- ✅ Cleaned up console.logs from tracking hooks
- ✅ Added agent deletion tracking
- ✅ Added agent name edit tracking
- ✅ Added tab navigation tracking
- ✅ Added document association tracking
- ✅ Enhanced file upload tracking in agent context
- ✅ Added library download tracking
- ✅ Added folder creation tracking
- ✅ Added file extraction tracking (basic & deep)
- ✅ Added PDF viewing tracking
- ✅ Comprehensive error tracking across all operations
- ✅ Extended `useDanaAnalytics` hook with new functions

---

**Last Updated**: January 1, 2025
**Maintainer**: Development Team
**Questions**: Refer to Product Manager or check `src/hooks/useAnalytics.ts`

