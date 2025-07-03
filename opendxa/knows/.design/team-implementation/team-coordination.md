# Team Coordination: Tonight's KNOWS vs RAG Sprint

**🎯 GOAL**: Working MVPs from both teams by end of night with comparative results

## Team Communication

### Primary Channels
- **Slack/Discord**: Real-time coordination
- **Shared Doc**: Live progress tracking
- **Git**: Code collaboration on `feat/knows-team` branch

### Check-in Schedule
- **Every 30 minutes**: Quick status updates
- **Phase gates**: Formal review before moving to next phase
- **Final demo**: Both teams present results

## Team KNOWS - Detailed Assignments

### CTN (Architecture Lead)
**Phase 0 (30 min)**:
- [ ] Create `opendxa/knows/mvp/` directory structure
- [ ] Define minimal `KnowledgeUnit` dataclass
- [ ] Set up basic Dana integration skeleton
- [ ] Define interfaces between team members' components

**Phase 1 (2-3 hours)**:
- [ ] Implement `KnowledgeComposer` class for context building
- [ ] Design Dana function signatures for knowledge retrieval
- [ ] Create knowledge-to-context formatting logic
- [ ] Integrate with Sang's Dana functions

**Phase 2 (1-2 hours)**:
- [ ] Coordinate integration testing
- [ ] Debug Dana runtime issues
- [ ] Optimize knowledge injection performance

### Sang (Implementation Lead)
**Phase 0 (30 min)**:
- [ ] Set up Dana function development environment
- [ ] Create basic Dana functions file: `knows_mvp_functions.py`
- [ ] Test Dana runtime integration points
- [ ] Set up testing framework structure

**Phase 1 (2-3 hours)**:
- [ ] Implement Dana functions for knowledge retrieval
- [ ] Build runtime bridge between knowledge system and LLM
- [ ] Create feedback collection mechanism (basic logging)
- [ ] Write unit tests for all functions

**Phase 2 (1-2 hours)**:
- [ ] Integration testing with CTN's components
- [ ] Performance optimization and debugging
- [ ] Ensure Dana agent executes reliably

### William (Data & Evaluation Lead)
**Phase 0 (30 min)**:
- [ ] Define use case and gather relevant knowledge content
- [ ] Set up evaluation metrics framework
- [ ] Create initial knowledge unit templates
- [ ] Prepare test case datasets

**Phase 1 (2-3 hours)**:
- [ ] Create 15-20 high-quality knowledge units for use case
- [ ] Implement evaluation metrics and comparison framework
- [ ] Design test cases with clear success criteria
- [ ] Build performance tracking dashboard (simple)

**Phase 2 (1-2 hours)**:
- [ ] Run comprehensive testing on both agents
- [ ] Analyze performance differences
- [ ] Document results and insights

## Team RAG - Coordination

### Requirements for Fair Comparison
- [ ] Use identical test cases as Team KNOWS
- [ ] Implement similar performance monitoring
- [ ] Ensure comparable response formats
- [ ] Document baseline approach for analysis

### Deliverables
- [ ] Functioning RAG agent with vector retrieval
- [ ] Performance metrics collection
- [ ] Results in comparable format to KNOWS team

## Shared Infrastructure

### Git Workflow
1. All work on `feat/knows-team` branch
2. Team KNOWS: `opendxa/knows/mvp/` directory
3. Team RAG: `opendxa/rag_baseline/` directory (create as needed)
4. Frequent commits with clear messages
5. No merge conflicts - coordinate file changes

### Testing Strategy
```bash
# Each team maintains their own tests
uv run pytest tests/knows/mvp/ -v      # KNOWS team
uv run pytest tests/rag_baseline/ -v   # RAG team

# Shared comparison tests
uv run pytest tests/comparison/ -v     # Both teams
```

### Data/Configuration
- Shared test cases in `tests/comparison/test_cases.json`
- Shared evaluation metrics in `tests/comparison/metrics.py`
- Knowledge units in `opendxa/knows/mvp/knowledge/`

## Critical Dependencies

### Team KNOWS Dependencies
1. **CTN → Sang**: Knowledge unit schema → Dana function signatures
2. **William → CTN**: Knowledge units → Context composer
3. **Sang → William**: Dana agent → Evaluation framework

### Cross-Team Dependencies
1. **William (KNOWS) → Team RAG**: Test cases and evaluation metrics
2. **Both teams → Shared**: Identical use case definition

## Risk Mitigation Plan

### High-Priority Risks
| Risk | Mitigation | Owner | Fallback |
|------|------------|--------|----------|
| Dana integration fails | Simple Python wrapper | Sang | Pure Python KNOWS implementation |
| Knowledge quality low | Focus on fewer, better units | William | Use existing KNOWS examples |
| Time overrun | Reduce scope to core comparison | CTN | Simplify evaluation metrics |
| Teams diverge | 30-min check-ins | All | Re-align on shared test cases |

### Communication Escalation
1. **Issue**: Try to solve within team (15 min)
2. **Escalate**: Cross-team discussion (15 min)
3. **Decide**: Architecture call with CTN (10 min)
4. **Execute**: Clear assignment and timeline

## Success Criteria (End of Night)

### Minimum Viable Success
- [ ] Both agents respond to same test cases
- [ ] KNOWS agent shows measurable difference vs RAG
- [ ] Results documented with clear comparison
- [ ] Team can explain advantages/trade-offs

### Stretch Goals
- [ ] KNOWS agent demonstrates ≥20% improvement
- [ ] Clear explainability advantage
- [ ] Feedback mechanism shows learning potential
- [ ] Ready for demo/presentation

## Timeline Checkpoints

| Time | Checkpoint | Expected Status |
|------|------------|-----------------|
| +30 min | Phase 0 Complete | Development environments ready |
| +2 hours | Phase 1 Midpoint | Core components implemented |
| +3.5 hours | Phase 1 Complete | Both agents functional |
| +4.5 hours | Phase 2 Complete | Testing and integration done |
| +5.5 hours | Phase 3 Complete | Results documented, demo ready |

**Let's ship it! 🚀** 