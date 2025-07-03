### NB: CLICK ON "PREVIEW" AND CHOOSE FROM ONE OF THESE TEMPLATES:

* [Developer Contrib](?template=contrib.md)
* [Agent Framework](?template=agent.md)
* [Dana Language and Sandbox](?template=dana.md)
* [Documentation](?template=docs.md)
* [General/Other](?template=general.md)

## 🎯 **PR Overview**

<!-- Brief description of what this PR accomplishes -->

### **Key Features**
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

---

## 🚀 **Review Instructions**

### **Prerequisites**
```bash
# Ensure you're on the PR branch
git checkout [branch-name]

# Install dependencies
uv sync

# Verify Python environment
python --version  # Should be 3.12+
```

### **How to Test**

<!-- Add specific testing instructions for this PR -->

```bash
# Example test commands
uv run pytest tests/ -v
python examples/example_script.py
```

### **What to Expect**

<!-- Describe what reviewers should see when running the code -->

---

## 🔍 **Review Checklist**

### **Core Functionality**
- [ ] **Code runs successfully** without errors
- [ ] **All features** are implemented as described
- [ ] **Performance** meets requirements
- [ ] **Edge cases** are handled properly
- [ ] **Error handling** is comprehensive

### **Code Quality**
- [ ] **Type hints** throughout all Python files
- [ ] **Comprehensive documentation** and comments
- [ ] **Modular design** with clear separation of concerns
- [ ] **Test coverage** for core functionality
- [ ] **Follows project standards** and conventions

### **Business Value**
- [ ] **Clear business scenarios** with realistic requirements
- [ ] **Performance improvements** over existing approaches
- [ ] **ROI impact** with specific metrics
- [ ] **User experience** is intuitive and efficient

---

## 📊 **Key Files to Review**

<!-- List the most important files for reviewers to focus on -->

- `path/to/key/file.py` - Brief description
- `path/to/another/file.py` - Brief description

---

## 🎯 **Success Criteria**

The PR is ready for merge when:
1. **All tests pass** without failures
2. **Code review** is completed and approved
3. **Documentation** is updated and clear
4. **Performance** meets requirements
5. **Security** considerations are addressed

---

## 🚨 **Common Issues to Watch For**

### **Runtime Issues**
- **Import errors**: Check module dependencies
- **Path issues**: Verify file paths and working directory
- **Version compatibility**: Ensure Python version requirements

### **Code Issues**
- **Missing error handling**: Look for unhandled exceptions
- **Performance bottlenecks**: Check for inefficient algorithms
- **Security vulnerabilities**: Review input validation and sanitization

---

## 💰 **Business Value Summary**

<!-- Summarize the business impact and value of this PR -->

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**
