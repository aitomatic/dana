# 🏠 Smart HVAC Demo

This demo showcases the power of POET (Perceive → Operate → Enforce → Train) by comparing two HVAC control systems side-by-side:

- **Left Side (Basic HVAC)**: Traditional SENSE + ACT approach
- **Right Side (POET HVAC)**: Enhanced SENSE + THINK + ACT approach

## Key Demonstrations

### Basic HVAC System
- **Manual Control**: User must manually adjust thermostat target temperature
- **Simple Logic**: Basic proportional control (same code as POET system)
- **No Learning**: Static parameters, no optimization
- **User Burden**: Requires constant manual adjustments

### POET HVAC System  
- **Comfort-Based Control**: User just clicks "Too Hot" / "Too Cold" / "Comfortable"
- **Same Logic**: Identical control algorithm, enhanced by POET
- **Automatic Learning**: Learns optimal setpoints from user feedback
- **Intelligence Added**: Domain expertise, energy optimization, equipment protection

## Expected Results

The demo shows that POET achieves:
- **Higher Comfort Score**: Better temperature control with fewer oscillations
- **Lower Energy Consumption**: Intelligent optimization reduces waste
- **Less User Effort**: Comfort feedback vs manual thermostat adjustments

## Architecture

```
Basic HVAC: User Input → Simple Control Logic → HVAC Output
POET HVAC:  User Feedback → POET Enhancement → Simple Control Logic → HVAC Output
```

The key insight: **The business logic is identical**. POET adds the intelligence through:
- **P**: Input optimization (setpoint adjustment)
- **O**: Reliable execution (retries, error handling)
- **E**: Output validation (equipment protection, safety)
- **T**: Learning optimization (comfort patterns, energy efficiency)

## Running the Demo

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure POET is available (from parent dana project)
export PYTHONPATH="/path/to/dana.poet:$PYTHONPATH"
```

### Start the Demo

```bash
# From the demos/smart_hvac directory
python main.py
```

### Open in Browser

Visit: http://localhost:8000

## Demo Flow

1. **Start Demo**: Click "Start Demo" to begin the simulation
2. **Basic System**: 
   - Adjust thermostat using +/- buttons
   - Click "Set Temperature" to apply
   - Watch energy usage and comfort scores
3. **POET System**:
   - Click "Too Cold", "Comfortable", or "Too Hot" 
   - Watch POET learn and optimize automatically
   - Observe improved performance metrics
4. **Compare Results**: 
   - Real-time charts show temperature, energy, and comfort
   - Summary statistics show cumulative benefits
   - POET learning status displays optimization progress

## Key Features

### Real-Time Visualization
- **Temperature Tracking**: Both room and target temperatures
- **Energy Monitoring**: Instantaneous and cumulative consumption
- **Comfort Scoring**: Calculated based on temperature stability and user feedback
- **HVAC Status**: Heating/cooling outputs, fan speeds, system modes

### Room Physics Simulation
- **Thermal Mass**: Realistic temperature response
- **Weather Effects**: Outdoor temperature influences
- **Heat Gains**: Occupancy and equipment loads
- **Equipment Modeling**: Realistic HVAC capacity and efficiency

### POET Learning Display
- **Algorithm Status**: Shows statistical learning in action
- **Execution Metrics**: Success rates, retry counts
- **Learning Recommendations**: Real-time optimization suggestions
- **Parameter Evolution**: Tracks learned parameter changes

## Technical Implementation

### Backend (FastAPI)
- **WebSocket Communication**: Real-time updates
- **Room Simulation**: Physics-based thermal modeling
- **POET Integration**: Uses actual POET decorator
- **Metrics Collection**: Comprehensive performance tracking

### Frontend (JavaScript + Chart.js)
- **Real-Time Charts**: Live updating visualizations
- **User Controls**: Intuitive interface for both systems
- **Status Monitoring**: Connection and system health
- **Responsive Design**: Works on desktop and mobile

### POET Framework
- **Statistical Learning**: Online parameter optimization
- **Domain Intelligence**: Building management plugin
- **Performance Tracking**: Comprehensive metrics collection
- **Feedback Processing**: User comfort learning

## Demo Scenarios

### Scenario 1: Morning Startup
- Both systems start at setback temperature
- Basic: User must manually adjust thermostat
- POET: Learns optimal comfort temperature from feedback

### Scenario 2: Changing Weather
- Outdoor temperature affects building load
- Basic: Requires manual thermostat adjustments
- POET: Automatically adapts to maintain comfort

### Scenario 3: Energy Efficiency
- Compare energy consumption patterns
- Basic: Fixed control strategy
- POET: Optimizes for comfort + efficiency balance

## Expected Demonstration Results

After 20-30 minutes of simulation:

| Metric | Basic HVAC | POET HVAC | Improvement |
|--------|------------|-----------|-------------|
| Avg Comfort Score | 75-85 | 85-95 | +10-15% |
| Energy Consumption | Baseline | 15-25% less | 15-25% savings |
| User Adjustments | 8-12 manual | 3-5 feedback | 60% reduction |
| Temperature Stability | ±2°F swings | ±1°F swings | 50% better |

## Code Insights

The demo shows that both systems use **identical control logic**:

```python
# Both systems use this same function
def hvac_control(current_temp, target_temp, outdoor_temp, occupancy):
    temp_error = target_temp - current_temp
    
    if abs(temp_error) < 0.5:
        return HVACCommand(0, 0, 20, "idle")
    elif temp_error > 0:
        output = min(100, abs(temp_error) * 20)
        return HVACCommand(output, 0, output+20, "heating")
    else:
        output = min(100, abs(temp_error) * 20)
        return HVACCommand(0, output, output+20, "cooling")
```

**The only difference**: The POET version has `@poet(domain="building_management")` decorator!

This demonstrates POET's core value: **Transform simple business logic into enterprise-grade systems with a single line of code.**

## Troubleshooting

### WebSocket Connection Issues
- Check firewall settings
- Ensure port 8000 is available
- Verify CORS settings if accessing from different domain

### POET Import Errors
- Ensure PYTHONPATH includes dana project
- Check that all dependencies are installed
- Verify Python version compatibility (3.9+)

### Simulation Performance
- Reduce update frequency if CPU usage is high
- Check browser developer tools for JavaScript errors
- Ensure adequate system memory for real-time updates

## Extending the Demo

### Additional Features
- **Weather Patterns**: Implement realistic daily/seasonal cycles
- **Occupancy Schedules**: Add realistic building usage patterns  
- **Equipment Failures**: Show POET's resilience to system issues
- **Multiple Zones**: Expand to multi-zone HVAC control

### Learning Enhancements
- **LLM Integration**: Add language model reasoning
- **Predictive Control**: Anticipate occupancy and weather
- **Cross-Building Learning**: Share insights between buildings
- **Advanced Objectives**: Multi-objective optimization

This demo effectively showcases POET's ability to enhance simple business logic with enterprise intelligence, learning, and optimization - all while maintaining the same underlying code structure.