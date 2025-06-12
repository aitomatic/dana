# Smart HVAC Demo - Real POET Integration

This demo has been enhanced to use the **real POET framework** instead of the mock decorator, enabling actual LLM-powered reasoning and learning capabilities.

## 🚀 Key Enhancements

### 1. **Real POET Framework Integration**
- **File**: `hvac_systems.py`
- **Import**: `from opendxa.dana.poet.poet import poet`
- **Plugin**: Automatic discovery of `building_management` domain plugin
- **Fallback**: Graceful fallback to mock if imports fail

### 2. **LLM-Powered Reasoning**
- **File**: `llm_integration.py`
- **Features**:
  - Comfort optimization analysis
  - Energy efficiency recommendations
  - Feedback pattern analysis
  - Multi-provider LLM support

### 3. **Building Management Plugin**
- **Plugin**: `building_management`
- **Capabilities**:
  - Input processing with thermal intelligence
  - Equipment protection and validation
  - Energy optimization strategies
  - Learning parameter adaptation

## 🔧 Setup Instructions

### 1. **Install Dependencies**
```bash
# Ensure you have the OpenDXA package installed
pip install -e .  # From the opendxa.poet root directory
```

### 2. **Configure LLM Access**
Set at least one API key in your environment:

```bash
# OpenAI (recommended)
export OPENAI_API_KEY="your-openai-api-key"

# OR Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# OR Groq (fast and free)
export GROQ_API_KEY="your-groq-api-key"
```

### 3. **Run the Demo**
```bash
cd demos/smart_hvac
python main.py
```

Visit http://localhost:8000 to see the enhanced demo.

## 🎯 How to Use the Real POET Decorator

### Basic Usage
```python
from opendxa.dana.poet.poet import poet

@poet(domain="building_management")
def my_hvac_function(temp, setpoint, occupancy, outdoor_temp):
    # Your HVAC logic here
    return hvac_command
```

### Advanced Usage with Learning
```python
@poet(
    domain="building_management",
    enable_training=True,
    learning_algorithm="statistical",
    learning_rate=0.05,
    performance_tracking=True
)
def smart_hvac_function(temp, setpoint, occupancy, outdoor_temp):
    # Same logic, but POET adds:
    # - Input optimization (Perceive)
    # - Retry logic (Operate) 
    # - Output validation (Enforce)
    # - Parameter learning (Train)
    return hvac_command
```

## 🧠 LLM Integration Features

### 1. **Comfort Reasoning**
The LLM analyzes user feedback and suggests temperature adjustments:
```python
llm_manager = get_llm_manager()
analysis = await llm_manager.reason_about_comfort(
    current_temp=72.0,
    target_temp=71.0,
    user_feedback="too_cold",
    comfort_history=feedback_history
)
```

### 2. **Energy Optimization**
LLM provides energy-saving strategies:
```python
optimization = await llm_manager.reason_about_energy_optimization(
    current_temp=72.0,
    target_temp=70.0,
    outdoor_temp=85.0,
    occupancy=True
)
```

### 3. **Pattern Analysis**
LLM identifies patterns in user behavior:
```python
patterns = await llm_manager.analyze_feedback_patterns(feedback_history)
```

## 🔍 What Changes When Using Real POET

### Before (Mock POET):
- Static responses
- No real learning
- No LLM integration
- Fixed optimization

### After (Real POET):
- **Perceive**: Building management plugin processes inputs with thermal intelligence
- **Operate**: Retry logic, timeout handling, error recovery
- **Enforce**: Equipment protection, safety validation, energy optimization
- **Train**: Statistical learning from execution results and user feedback

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HVAC Demo     │───▶│   POET Framework │───▶│ Building Mgmt   │
│   (main.py)     │    │   (poet.py)      │    │ Plugin          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ LLM Integration │    │ Online Learning  │    │ Domain-Specific │
│ (llm_integration│    │ Components       │    │ Optimizations   │
│ .py)            │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Demo Features

### 1. **Real-time Learning Status**
- View POET's learning progress
- See parameter adjustments
- Monitor success rates

### 2. **LLM-Enhanced Feedback**
- Click "Too Hot/Cold" for intelligent adjustments
- LLM analyzes patterns and suggests optimizations
- Real-time reasoning displayed

### 3. **Energy Intelligence**
- Automatic energy optimization based on conditions
- LLM-powered strategy recommendations
- Adaptive setpoint management

## 🐛 Troubleshooting

### LLM Not Working?
1. Check API key is set: `echo $OPENAI_API_KEY`
2. Verify internet connection
3. Check demo console for error messages

### POET Import Errors?
1. Ensure you're in the correct directory
2. Install with `pip install -e .` from project root
3. Check Python path includes opendxa package

### Plugin Not Loading?
1. Check console for plugin discovery messages
2. Verify plugin files exist in `opendxa/dana/poet/plugins/`
3. Check plugin registry initialization

## 🎓 Learning More

- **POET Documentation**: `docs/design/02_dana_runtime_and_execution/poet_functions.md`
- **Plugin Development**: `opendxa/dana/poet/plugins/base.py`
- **LLM Resource Guide**: `opendxa/common/resource/llm_resource.py`

## 🎯 Next Steps

1. **Add More Sensors**: Extend with humidity, CO2, air quality
2. **Custom Plugins**: Create domain-specific plugins for your use case
3. **Advanced Learning**: Experiment with different learning algorithms
4. **Real Hardware**: Connect to actual HVAC systems

---

🎉 **Enjoy exploring the real POET framework!** This demo showcases the power of declarative AI with domain expertise, learning, and LLM integration.