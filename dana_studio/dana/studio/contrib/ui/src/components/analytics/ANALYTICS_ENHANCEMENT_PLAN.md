# Analytics Enhancement Plan - PM-Focused Insights

## Current State Assessment

### ✅ What We Track Now (Good)

- Page views
- Agent CRUD operations
- File operations
- Basic error tracking
- Tab navigation

### ❌ Critical Gaps for Product Decisions

#### 1. **NO USER CONTEXT**

- Can't distinguish new vs returning users
- No user cohorts or segments
- Can't track user progression/maturity

#### 2. **NO FUNNEL TRACKING**

- Can't measure conversion rates
- No drop-off point identification
- Missing "jobs to be done" tracking

#### 3. **NO ENGAGEMENT METRICS**

- Time spent on tasks
- Session depth (actions per session)
- Feature stickiness

#### 4. **NO SUCCESS METRICS**

- Agent quality/success rate
- File extraction ROI
- User satisfaction signals

#### 5. **NO DISCOVERY TRACKING**

- First-time feature usage
- Feature adoption rate
- User onboarding completion

---

## PM Questions We CAN'T Answer Yet

### User Acquisition & Activation

- ❌ What % of new users create their first agent?
- ❌ How long does it take from signup to first value?
- ❌ What's the activation funnel? (visit → agent → chat → success)

### Retention & Engagement

- ❌ What brings users back? (retention drivers)
- ❌ What's the D1/D7/D30 retention curve?
- ❌ Which users become power users?

### Feature Value

- ❌ Which features drive retention?
- ❌ What's the ROI of deep extraction vs basic?
- ❌ Do users who use X feature stay longer?

### User Friction

- ❌ Where do users get stuck?
- ❌ What % abandon agent creation?
- ❌ Which errors cause users to leave?

### Content & Quality

- ❌ Which agent types are most successful?
- ❌ What document types drive best results?
- ❌ Do users iterate on agents? How many times?

---

## Enhancement Recommendations

### Priority 1: USER IDENTITY & SEGMENTATION (High Impact)

**Add User Properties:**

```typescript
// Set once per user
analytics.setUserProperties({
  user_id: userId,
  user_type: 'free' | 'pro' | 'enterprise',
  signup_date: '2025-01-01',
  total_agents_created: 5,
  feature_tier: 'advanced',
  organization_id: 'org_123',
});
```

**Track User Lifecycle Events:**

- `user_signup` - New user registered
- `user_first_agent` - First agent created (activation!)
- `user_first_chat` - First chat interaction (aha moment!)
- `user_power_action` - Performed 10+ actions in session
- `user_retention_milestone` - Day 1, 7, 30 return

**Value:** Segment users, track cohorts, measure activation

---

### Priority 2: FUNNEL & CONVERSION TRACKING (High Impact)

**Agent Creation Funnel:**

```typescript
1. Click "Create Agent" → track: funnel_start (agent_creation)
2. Enter name → track: funnel_step (agent_creation, step_1_name)
3. Add description → track: funnel_step (agent_creation, step_2_description)
4. Add resources → track: funnel_step (agent_creation, step_3_resources)
5. Submit → track: funnel_complete (agent_creation)
```

**Key Funnels to Track:**

- Agent creation (start → complete)
- File extraction (upload → extract → save)
- Chat engagement (start → message → response)
- Onboarding (visit → agent → chat → success)

**Abandonment Tracking:**

```typescript
// Track when users leave mid-process
trackEvent({
  action: 'funnel_abandon',
  category: 'conversion',
  label: 'agent_creation_step_2',
  value: timeSpent,
});
```

**Value:** Identify where users drop off, optimize conversion

---

### Priority 3: ENGAGEMENT & SUCCESS METRICS (Medium Impact)

**Time-based Metrics:**

```typescript
// Track time spent on tasks
const startTime = Date.now();
// ... user performs action ...
trackTiming('agent_creation_duration', Date.now() - startTime);
trackTiming('file_extraction_duration', duration);
trackTiming('chat_session_duration', sessionTime);
```

**Engagement Depth:**

```typescript
// Track session quality
trackEvent({
  action: 'session_complete',
  category: 'engagement',
  label: 'high_engagement', // based on action count
  value: totalActions,
});
```

**Success Signals:**

```typescript
// Track outcomes
trackEvent({
  action: 'agent_first_success',
  category: 'success',
  label: agentId,
});

trackEvent({
  action: 'extraction_saved',
  category: 'success',
  label: fileType,
  value: pageCount,
});
```

**Value:** Measure actual value delivery, not just feature usage

---

### Priority 4: FEATURE DISCOVERY & ADOPTION (Medium Impact)

**First-Time Usage:**

```typescript
// Track feature discovery
trackEvent({
  action: 'feature_first_use',
  category: 'discovery',
  label: 'deep_extraction',
});

trackEvent({
  action: 'feature_first_use',
  category: 'discovery',
  label: 'pdf_viewer',
});
```

**Feature Adoption Rate:**

```typescript
// Track ongoing usage
trackEvent({
  action: 'feature_used',
  category: 'adoption',
  label: 'deep_extraction',
  value: usageCount,
});
```

**Onboarding Progress:**

```typescript
trackEvent({
  action: 'onboarding_step_complete',
  category: 'activation',
  label: 'step_1_create_agent',
});
```

**Value:** Understand feature stickiness, optimize onboarding

---

### Priority 5: ENHANCED ERROR & FRICTION TRACKING (High Impact)

**Context-Rich Error Tracking:**

```typescript
trackError({
  errorType: 'agent_creation_failed',
  errorMessage: error.message,
  errorCode: error.code,
  context: {
    userId: userId,
    agentName: agentName,
    attemptNumber: 2,
    previousAction: 'added_documents',
    timeInFlow: 45000, // 45 seconds
  },
});
```

**Friction Points:**

```typescript
// Track when things take too long
if (duration > 5000) {
  trackEvent({
    action: 'slow_operation',
    category: 'performance',
    label: 'file_extraction',
    value: duration,
  });
}
```

**Value:** Prioritize bug fixes by user impact

---

### Priority 6: SESSION & JOURNEY TRACKING (Medium Impact)

**Session Metadata:**

```typescript
// Set at session start
sessionStorage.setItem('session_id', generateSessionId());
sessionStorage.setItem('session_start', Date.now());
sessionStorage.setItem('entry_point', window.location.pathname);
```

**Journey Tracking:**

```typescript
// Track user paths
trackEvent({
  action: 'journey_step',
  category: 'navigation',
  label: 'agents_list → agent_detail → chat',
  value: stepNumber,
});
```

**Value:** Understand typical user journeys, optimize flows

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

1. ✅ Add user property setting
2. ✅ Implement session tracking
3. ✅ Add first-time usage detection
4. ✅ Enhanced error context

### Phase 2: Funnels (Week 2)

1. ✅ Agent creation funnel
2. ✅ File extraction funnel
3. ✅ Chat engagement funnel
4. ✅ Abandonment tracking

### Phase 3: Engagement (Week 3)

1. ✅ Time-based metrics for key tasks
2. ✅ Session quality tracking
3. ✅ Success signal tracking
4. ✅ Power user identification

### Phase 4: Optimization (Week 4)

1. ✅ A/B test infrastructure
2. ✅ Custom dashboards
3. ✅ Automated alerts
4. ✅ Weekly PM reports

---

## Expected PM Insights After Enhancement

### Week 1 (Foundation)

- User cohort analysis
- New vs returning user behavior
- Feature adoption by user segment

### Week 2 (Funnels)

- Conversion rate by funnel
- Drop-off point identification
- Time-to-value metrics

### Week 3 (Engagement)

- Retention drivers
- Feature stickiness
- User lifecycle stages

### Week 4 (Optimization)

- A/B test results
- Feature experiment data
- Predictive churn signals

---

## Success Metrics for Analytics Itself

- ✅ Can answer "Why did user X churn?" in 5 minutes
- ✅ Can track any funnel conversion rate
- ✅ Can segment users by behavior
- ✅ Can identify top friction points
- ✅ Can measure feature ROI
- ✅ Can predict user outcomes

---

## Key Recommendations Summary

### Must-Have (Do Now)

1. **User identification & properties**
2. **Funnel tracking for agent creation**
3. **Success signals (first agent, first chat)**
4. **Enhanced error context**

### Should-Have (Do Next)

1. **Time-based metrics for key tasks**
2. **Feature first-use tracking**
3. **Session quality metrics**
4. **Journey path tracking**

### Nice-to-Have (Do Later)

1. **A/B test infrastructure**
2. **Predictive analytics**
3. **Custom PM dashboards**
4. **Automated insights reports**

---

**Next Steps:** Implement Priority 1 (User Identity) and Priority 2 (Funnels) for maximum PM value.
