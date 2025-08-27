# SMBC Credit Approval System - Streamlit Web Interface

A modern, professional web interface for the Dana credit approval agent that demonstrates real-time credit decisioning capabilities.

## Features

### 🏦 Professional Banking Interface
- **SMBC Credit Approval System** branding
- Professional gradient header with banking aesthetics
- Responsive 2-column layout (60% application, 40% chat)

### 📊 UCI Dataset Integration
- Load real UCI credit dataset cases (1-690)
- Automatic mapping of UCI data to application format
- Real-time case loading with validation

### 📋 Application Processing
- **Manual Application Form**: Complete credit application with all required fields
- **Real Dana Agent Integration**: Direct calls to Dana agent workflows
- **Decision Summary**: Professional decision cards with metrics
- **Error Handling**: Graceful fallbacks when Dana agent unavailable

### 💬 Dana Agent Chat Interface
- **Real-time Chat**: Direct communication with Dana agent
- **Quick Action Buttons**:
  - 🔍 Analyze Application
  - ⚠️ Risk Factors
  - 📋 Compliance Check
  - 💡 Explain Decision
- **Chat History**: Persistent conversation tracking
- **Context Awareness**: Chat with application context

## Technical Architecture

### Dana Agent Integration
```python
# Real Dana agent loading
agent = dana.load_agent("CreditApprovalSystem")

# Direct workflow calls
result = agent.workflows.credit_approval_pipeline(app_data)

# Real-time reasoning
response = agent.reason(user_message, context=app_data)
```

### UCI Dataset Processing
```python
# Load UCI dataset from crx.data
df = pd.read_csv('credit+approval/crx.data', header=None, names=columns)

# Map to application format
application = {
    "applicant_id": f"UCI-{case_number:03d}",
    "name": f"Applicant {case_number}",
    "age": int(case['age']),
    "employment_type": "permanent" if case['employment'] in ['a', 'b'] else "contract",
    # ... more mappings
}
```

### Key Functions
- `load_uci_case(case_number)`: Load and format UCI dataset cases
- `process_application(app_data)`: Real Dana agent processing
- `chat_with_dana(user_message, context)`: Real-time agent communication
- `analyze_application(app_data)`: Credit risk analysis
- `check_risk_factors(app_data)`: Risk factor identification
- `check_compliance(app_data)`: Regulatory compliance checking
- `explain_decision(app_data)`: Decision explanation

## Installation & Setup

### Prerequisites
```bash
# Install Dana
pip install dana

# Install Streamlit dependencies
pip install streamlit pandas
```

### Running the Application
```bash
# Option 1: Use the provided script
./run_streamlit_app.sh

# Option 2: Direct Streamlit command
streamlit run streamlit_app.py --server.port 8501
```

### Access the Interface
Open your browser and navigate to: **http://localhost:8501**

## Usage Guide

### 1. Load UCI Dataset Case
1. Enter a case number (1-690) in the "Load UCI Case" field
2. Click "📂 Load Case" button
3. Review the loaded application data

### 2. Process Application
1. Fill out the credit application form with applicant details
2. Click "🚀 Process Application" to submit to Dana agent
3. Review the decision summary with metrics

### 3. Chat with Dana Agent
1. Use quick action buttons for common queries
2. Type custom messages in the chat input
3. Review chat history for conversation context

### 4. Real-time Analysis
- **Analyze Application**: Get comprehensive credit analysis
- **Risk Factors**: Identify potential risk factors
- **Compliance Check**: Verify regulatory compliance
- **Explain Decision**: Get detailed decision reasoning

## File Structure

```
examples/06_real_time_credit_approval/
├── streamlit_app.py              # Main Streamlit application
├── run_streamlit_app.sh          # Run script
├── requirements.txt              # Dependencies
├── agent.na                     # Dana agent definition
├── workflows.na                 # Credit approval workflows
├── knowledge.na                 # Banking knowledge base
├── resources.na                 # External resources
└── credit+approval/
    └── crx.data                 # UCI credit dataset
```

## Technical Features

### Error Handling
- Graceful fallbacks when Dana agent unavailable
- Comprehensive error messages and logging
- Session state management for persistence

### Performance
- Efficient UCI dataset loading
- Real-time agent communication
- Responsive UI with professional styling

### Security
- Input validation for all form fields
- Safe error handling without exposing internals
- Professional banking-grade interface

## Customization

### Styling
The app uses custom CSS for professional banking aesthetics:
- Gradient headers
- Decision cards with color coding
- Chat message styling
- Professional metrics display

### Agent Integration
Modify the Dana agent integration in:
- `initialize_dana_agent()`: Agent loading
- `process_application()`: Workflow calls
- `chat_with_dana()`: Reasoning interface

### Dataset Integration
Customize UCI dataset processing in:
- `load_uci_dataset()`: Dataset loading
- `load_uci_case()`: Case mapping

## Troubleshooting

### Common Issues

1. **Dana Agent Not Available**
   - Ensure Dana is properly installed: `pip install dana`
   - Check agent files are in the correct directory
   - Verify agent.na, workflows.na, knowledge.na, resources.na exist

2. **UCI Dataset Not Loading**
   - Verify crx.data file exists in credit+approval/ directory
   - Check file permissions and format

3. **Streamlit Not Starting**
   - Install dependencies: `pip install -r requirements.txt`
   - Check port availability (default: 8501)
   - Verify Python environment

### Debug Mode
Run with debug information:
```bash
streamlit run streamlit_app.py --logger.level debug
```

## Performance Notes

- **Agent Initialization**: Dana agent loads once per session
- **Dataset Loading**: UCI dataset cached for performance
- **Chat History**: Stored in session state for persistence
- **Real-time Processing**: Direct Dana agent calls for immediate responses

## Future Enhancements

- **Multi-language Support**: Japanese banking interface
- **Advanced Analytics**: Detailed credit scoring visualization
- **Audit Trail**: Complete decision audit logging
- **Integration APIs**: External system connectivity
- **Mobile Optimization**: Responsive mobile interface

---

**Built with Dana AI** - Real-time credit decisioning powered by intelligent agents. 