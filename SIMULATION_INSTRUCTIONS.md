# KNOWS CORRAL Simulation Instructions

## 🚀 **How to Run the Simulations**

### **Prerequisites**
```bash
# Ensure you're on the PR branch
git checkout feat/knows-team

# Install dependencies
uv sync

# Verify Python environment
python --version  # Should be 3.12+
```

### **Option 1: Knowledge Evolution Simulations (Recommended)**

These simulations show how KNOWS improves performance over multiple iterations.

#### **Semiconductor Packaging Use Case**
```bash
cd opendxa/knows/.design/use-cases/semiconductor-packaging-vision-alignment
python knowledge_evolution_simulation.py
```

#### **IC Design FAE Use Case**
```bash
cd opendxa/knows/.design/use-cases/ic-design-fae-customer-support
python knowledge_evolution_simulation.py
```

### **Option 2: Basic CORRAL Simulations**

These show a single execution of the CORRAL lifecycle.

```bash
# Semiconductor use case
cd opendxa/knows/.design/use-cases/semiconductor-packaging-vision-alignment
python corral_simulation.py

# FAE use case
cd opendxa/knows/.design/use-cases/ic-design-fae-customer-support
python corral_simulation.py
```

---

## 📊 **What the Simulations Do**

### **Knowledge Evolution Simulation**

This simulation demonstrates how KNOWS transforms knowledge-intensive processes through iterative learning:

1. **Initial Setup**: Creates basic knowledge base with documentary knowledge
2. **5 Iterations**: Each iteration runs the complete CORRAL lifecycle
3. **Performance Tracking**: Measures success rates, response times, and satisfaction
4. **Knowledge Growth**: Tracks new knowledge creation and promotion
5. **Final Analysis**: Compares results with traditional RAG approaches

### **CORRAL Lifecycle Phases**

Each iteration executes all 6 phases:

1. **CURATE**: Analyzes requirements and identifies knowledge needs
2. **ORGANIZE**: Creates knowledge units and stores them appropriately
3. **RETRIEVE**: Selects relevant knowledge for the current task
4. **REASON**: Composes knowledge into actionable insights
5. **ACT**: Executes the task using composed knowledge
6. **LEARN**: Analyzes outcomes and updates the knowledge base

### **Business Scenarios**

#### **Semiconductor Packaging**
- **Challenge**: Calibrating vision system for BGA packages with non-standard fiducial patterns
- **Requirements**: ±0.1mm accuracy, High-Tg FR4 substrate material
- **Goal**: Reduce setup time from 2-3 days to 4-6 hours

#### **IC Design FAE Support**
- **Challenge**: Supporting medical device customers with power management IC implementation
- **Requirements**: FDA Class III compliance, ultra-low power, 99.99% reliability
- **Goal**: Improve support success rates and customer satisfaction

---

## 📈 **How to Interpret the Results**

### **Key Metrics to Watch**

#### **Performance Improvements Over Iterations**
```
Iteration 1: Success 68.0% | Response 105min | Satisfaction 79.8%
Iteration 2: Success 76.0% | Response 90min  | Satisfaction 94.0%
Iteration 3: Success 84.0% | Response 75min  | Satisfaction 95.0%
Iteration 4: Success 92.0% | Response 60min  | Satisfaction 95.0%
Iteration 5: Success 95.0% | Response 45min  | Satisfaction 95.0%
```

**What This Means**: KNOWS learns from each iteration, improving success rates and reducing response times.

#### **Knowledge Evolution**
```
📈 Knowledge Growth: 5 new units (+125.0%)
🎯 Average Success Rate: 83.0%
⏱️  Average Response Time: 75 minutes
😊 Average Customer Satisfaction: 91.8%
```

**What This Means**: The system creates new knowledge and improves existing knowledge through experience.

#### **Knowledge Maturity Analysis**
```
🔰 Basic Knowledge: 1 iterations
🔄 Enhanced Knowledge: 2 iterations
🎯 Mature Knowledge: 2 iterations
```

**What This Means**: Knowledge progresses from basic documentary knowledge to mature experiential knowledge.

### **RAG Comparison Results**

```
📊 Success Rate: Traditional RAG 65.0% → KNOWS 93.5% (+44%)
⏱️  Response Time: Traditional RAG 90min → KNOWS 52min (-42%)
😊 Customer Satisfaction: Traditional RAG 60.0% → KNOWS 95.0% (+58%)
```

**What This Means**: KNOWS significantly outperforms traditional RAG systems in all key metrics.

### **Business Value Interpretation**

#### **Success Rate Improvement (68% → 95%)**
- **Traditional Approach**: Trial-and-error, inconsistent results
- **KNOWS Approach**: Systematic learning, predictable improvement
- **Business Impact**: Reduced rework, faster time-to-production

#### **Response Time Reduction (105 → 45 minutes)**
- **Traditional Approach**: Manual knowledge lookup, repeated research
- **KNOWS Approach**: Intelligent knowledge retrieval, learned patterns
- **Business Impact**: Faster customer support, reduced costs

#### **Customer Satisfaction Increase (80% → 95%)**
- **Traditional Approach**: Inconsistent support quality
- **KNOWS Approach**: Continuously improving support quality
- **Business Impact**: Higher customer retention, better reputation

---

## 🔍 **Understanding the Output Structure**

### **Phase-by-Phase Execution**

Each iteration shows detailed execution of all 6 CORRAL phases:

```
📚 PHASE 1: CURATE - Knowledge Requirements
🎯 BUSINESS CONTEXT: [What the business needs]
🏗️  INFRASTRUCTURE FRAMEWORK: [How the system works]
✅ CURATE: Identified X topical and Y procedural knowledge requirements

🗂️  PHASE 2: ORGANIZE - Knowledge Structure
🎯 BUSINESS CONTEXT: [How knowledge is organized]
🏗️  INFRASTRUCTURE FRAMEWORK: [Technical implementation]
✅ ORGANIZE: Created X knowledge units

🔍 PHASE 3: RETRIEVE - Knowledge Selection
🎯 BUSINESS CONTEXT: [What knowledge is needed]
🏗️  INFRASTRUCTURE FRAMEWORK: [Selection algorithms]
✅ RETRIEVE: Selected X knowledge units (avg confidence: 0.XX)

🧠 PHASE 4: REASON - Knowledge Composition
🎯 BUSINESS CONTEXT: [How knowledge is used]
🏗️  INFRASTRUCTURE FRAMEWORK: [Composition logic]
✅ REASON: Composed knowledge with confidence 0.XX

⚡ PHASE 5: ACT - Knowledge Application
🎯 BUSINESS CONTEXT: [Task execution]
🏗️  INFRASTRUCTURE FRAMEWORK: [Execution framework]
✅ ACT: Execution completed
   📊 Success Rate: XX.X%
   ⏱️  Response Time: XX minutes
   😊 Customer Satisfaction: XX.X%

📈 PHASE 6: LEARN - Knowledge Evolution
🎯 BUSINESS CONTEXT: [Learning outcomes]
🏗️  INFRASTRUCTURE FRAMEWORK: [Evolution mechanisms]
✅ LEARN: Knowledge evolution completed
   📈 New Knowledge Units: X
   🔄 Promoted Units: X
   📊 Performance Improvement: X.X%
```

### **Business vs Infrastructure Separation**

The output clearly separates:
- **🎯 BUSINESS CONTEXT**: What the business is trying to accomplish
- **🏗️ INFRASTRUCTURE FRAMEWORK**: How the KNOWS system works

This helps reviewers understand both the business value and technical implementation.

---

## 🎯 **What Success Looks Like**

### **Successful Simulation Run**
- ✅ All 6 CORRAL phases execute without errors
- ✅ Performance metrics improve over iterations
- ✅ Knowledge base grows with new units
- ✅ Final analysis shows clear advantages over traditional RAG
- ✅ Business value is clearly demonstrated

### **Expected Performance Improvements**
- **Success Rate**: Should improve from ~68% to ~95%
- **Response Time**: Should decrease from ~105 to ~45 minutes
- **Customer Satisfaction**: Should increase from ~80% to ~95%
- **Knowledge Growth**: Should show 100%+ increase in knowledge base

### **Red Flags to Watch For**
- ❌ Missing CORRAL phases in output
- ❌ Performance metrics not improving over iterations
- ❌ No knowledge growth or evolution
- ❌ Errors during phase execution
- ❌ Inconsistent formatting or structure

---

## 💡 **Key Insights from the Simulations**

### **1. Continuous Learning**
KNOWS doesn't just store knowledge—it learns from every interaction and improves over time.

### **2. Systematic Approach**
Instead of trial-and-error, KNOWS provides a systematic, repeatable approach to knowledge-intensive tasks.

### **3. Business Transformation**
The simulations show how KNOWS can transform complex, knowledge-intensive processes into predictable, efficient operations.

### **4. Measurable ROI**
Clear metrics demonstrate the business value: faster response times, higher success rates, and improved customer satisfaction.

---

**These simulations demonstrate the transformative potential of KNOWS in converting knowledge-intensive processes from trial-and-error to systematic, learning-based optimization systems.** 