# Analytics Documentation

This folder contains all analytics-related documentation and guides for the Dana Agent Studio UI.

## 📁 Structure

```
analytics/
├── README.md                           # This file - overview
├── ANALYTICS_TRACKING.md               # Technical implementation guide
├── PM_INSIGHTS_GUIDE.md               # Product Manager's guide to insights
├── ANALYTICS_ENHANCEMENT_PLAN.md      # Future enhancement roadmap
└── examples/                          # Code examples and snippets
    ├── basic-usage.ts
    ├── advanced-tracking.ts
    └── custom-events.ts
```

## 📚 Documentation Overview

### 🛠️ **ANALYTICS_TRACKING.md**

**For**: Developers, Technical Leads
**Purpose**: Complete technical documentation of the analytics implementation
**Contains**:

- Event catalog and naming conventions
- Implementation details
- Code examples
- Troubleshooting guide
- Coverage summary

### 📊 **PM_INSIGHTS_GUIDE.md**

**For**: Product Managers, Business Analysts
**Purpose**: How to use analytics for product decisions
**Contains**:

- Key metrics and KPIs
- GA4 query examples
- Dashboard setup instructions
- Actionable insights guide
- Success metrics targets

### 🚀 **ANALYTICS_ENHANCEMENT_PLAN.md**

**For**: Product Managers, Engineering Leads
**Purpose**: Roadmap for future analytics improvements
**Contains**:

- Current gaps analysis
- Enhancement phases
- Implementation priorities
- Expected outcomes

## 🎯 Quick Start

### For Developers

1. Read `ANALYTICS_TRACKING.md` for implementation details
2. Check `src/lib/analytics.ts` and `src/hooks/useAnalytics.ts`
3. Use `useDanaAnalytics()` hook in components

### For Product Managers

1. Read `PM_INSIGHTS_GUIDE.md` for insights guide
2. Set up GA4 dashboard (instructions included)
3. Track activation funnel and time-to-value metrics

### For Planning

1. Review `ANALYTICS_ENHANCEMENT_PLAN.md` for roadmap
2. Prioritize Phase 2 (funnel tracking) for next sprint
3. Plan user segmentation and A/B testing infrastructure

## 📈 Current Status

### ✅ Implemented (Phase 1)

- Page view tracking
- Agent lifecycle events
- File operations tracking
- Session context and user identification
- First-time usage detection
- Time-to-value metrics
- Error tracking with context

### ⏳ Planned (Phase 2)

- Funnel abandonment tracking
- Form interaction tracking
- Enhanced user properties
- A/B testing infrastructure

### 🔮 Future (Phase 3+)

- Predictive analytics
- Custom PM dashboards
- Automated insights reports
- Advanced segmentation

## 🛠️ Implementation Files

**Core Analytics**:

- `src/lib/analytics.ts` - Analytics singleton class
- `src/lib/constants.ts` - Configuration (GA_CONFIG)
- `src/hooks/useAnalytics.ts` - React hooks

**Usage Examples**:

- `src/components/delete-agent-dialog.tsx` - Agent deletion tracking
- `src/pages/Library/index.tsx` - Library operations tracking
- `src/pages/Agents/tabs/OverviewTab.tsx` - Agent edit tracking
- `src/stores/extraction-file-store.ts` - File extraction tracking

## 📊 Key Metrics

| Metric            | Event                                  | Target  | Current |
| ----------------- | -------------------------------------- | ------- | ------- |
| Activation Rate   | `user_first_agent` / `session_start`   | 50%+    | TBD     |
| Time-to-Value     | `time_to_first_agent`                  | < 5 min | TBD     |
| Aha Moment Rate   | `user_first_chat` / `user_first_agent` | 60%+    | TBD     |
| Feature Discovery | `feature_first_use` / sessions         | 25%+    | TBD     |

## 🔗 Related Files

**Configuration**:

- `src/lib/constants.ts` - GA_CONFIG settings
- `src/main.tsx` - Analytics initialization

**Components with Tracking**:

- All components in `src/pages/`
- Key components in `src/components/`
- Store files in `src/stores/`

## 📝 Contributing

### Adding New Events

1. Add to `useDanaAnalytics()` hook in `src/hooks/useAnalytics.ts`
2. Update `ANALYTICS_TRACKING.md` with new event details
3. Add usage examples to relevant components
4. Update `PM_INSIGHTS_GUIDE.md` if it affects PM metrics

### Documentation Updates

1. Keep technical docs in `ANALYTICS_TRACKING.md`
2. Keep PM insights in `PM_INSIGHTS_GUIDE.md`
3. Update roadmap in `ANALYTICS_ENHANCEMENT_PLAN.md`
4. Update this README when adding new files

## 🎓 Learning Resources

- [Google Analytics 4 Documentation](https://developers.google.com/analytics/devguides/collection/ga4)
- [GA4 Events Reference](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)
- [React Analytics Best Practices](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)

---

**Last Updated**: January 1, 2025
**Maintainer**: Development Team
**Questions**: Check documentation or ask in team chat
