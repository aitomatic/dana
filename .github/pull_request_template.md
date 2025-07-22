## Description
Brief description of the changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Workshop example update

## Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have run the workshop integration tests locally (if applicable)

### Workshop Integration Tests
If your changes affect workshop examples or Dana core functionality:

```bash
# Run basic workshop tests
python tests/integration/run_workshop_tests.py -v

# Run file validation
python tests/integration/run_workshop_tests.py --file-validation

# Run with MCP integration (if MCP-related changes)
python tests/integration/run_workshop_tests.py --with-mcp
```

## Workshop Examples Affected
If you modified workshop examples, list which ones:
- [ ] Language and runtime examples
- [ ] Agent examples
- [ ] System of agents examples
- [ ] Knowledge organization examples
- [ ] Python interoperability examples

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Workshop examples still work correctly (if applicable)

## Additional Notes
Any additional information that would be helpful for reviewers.
