# 🌱 Smart Greenhouse Demo

A visual demonstration of POET's learning capabilities applied to agriculture and greenhouse management.

## Overview

This demo showcases two greenhouse control systems side-by-side:

1. **Basic Greenhouse** (SENSE + ACT): Fixed schedules and thresholds
2. **POET Greenhouse** (SENSE + THINK + ACT): Adaptive learning control

Watch as POET learns to optimize plant growth, resource usage, and yield through real-time adaptation.

## Features

### 🌿 Plant Growth Simulation
- Realistic plant growth stages: seedling → vegetative → flowering → fruiting
- Health responses to environmental conditions
- Visual plant representation with emojis
- Growth stage progression based on care quality

### 🤖 POET Learning
- **Botanical Optimization**: AI algorithm specialized for plant growth
- **Adaptive Watering**: Learns optimal soil moisture thresholds
- **Smart Lighting**: Optimizes light timing and intensity for growth phases
- **Intelligent Nutrient Delivery**: Learns optimal feeding schedules
- **Resource Efficiency**: Minimizes water and energy while maximizing yield

### 📊 Real-Time Visualization
- Live comparison charts (health, growth, water usage, yield)
- Environmental monitoring (temperature, humidity, soil moisture, light)
- Resource efficiency metrics
- Learning progress and recommendations

### 🎮 Interactive Features
- **Growth Feedback**: Provide plant health observations to accelerate POET learning
- **Real-time Controls**: Start, stop, and reset simulations
- **Performance Comparison**: See POET improvements over basic control

## Key Learning Objectives

1. **Adaptive Optimization**: POET automatically adjusts parameters based on plant response
2. **Resource Efficiency**: Achieve better yields with less water and energy
3. **Human-AI Collaboration**: User feedback enhances AI learning
4. **Domain Expertise**: POET understands agricultural principles and constraints

## Architecture

### Systems Comparison

| Aspect | Basic Greenhouse | POET Greenhouse |
|--------|------------------|-----------------|
| Control Logic | Fixed schedules | Adaptive learning |
| Watering | Water when soil < 30% | Learns optimal thresholds |
| Lighting | 6 AM - 6 PM fixed | Optimizes timing per growth stage |
| Nutrients | Daily at 8 AM | Learns optimal delivery windows |
| Climate | Temperature-only | Multi-factor optimization |
| Efficiency | Standard resource usage | Minimizes waste, maximizes yield |

### Technical Components

- **Plant Simulator**: Realistic growth and health modeling
- **Environmental Simulation**: Temperature, humidity, light, soil dynamics
- **POET Integration**: Mock learning framework with progressive optimization
- **Real-time Dashboard**: WebSocket-based live updates
- **Metrics Tracking**: Historical data for comparison analysis

## Running the Demo

```bash
# Navigate to the demo directory
cd demos/smart_greenhouse

# Install dependencies (if needed)
uv install

# Start the demo server
python main.py
```

Open http://localhost:8001 in your browser to see the demo.

## Demo Flow

1. **Initial State**: Both systems start with identical seedling plants
2. **Basic Control**: Fixed schedules, no adaptation
3. **POET Learning**: Gradual optimization and improvement
4. **User Interaction**: Provide growth feedback to accelerate learning
5. **Performance Comparison**: Observe resource savings and yield improvements

## Expected Outcomes

After running for several growth cycles, POET should demonstrate:

- **Water Savings**: 15-25% reduction through optimal timing
- **Energy Efficiency**: Improved lighting and heating optimization
- **Yield Improvement**: 10-20% better crop production
- **Plant Health**: More consistent high health scores
- **Stress Reduction**: Lower stress levels through better care

## Educational Value

This demo illustrates key POET principles:

- **Same Logic + Learning**: Identical base algorithms enhanced by AI
- **Continuous Improvement**: Performance gets better over time
- **Domain Awareness**: Understanding of agricultural constraints
- **Resource Optimization**: Balancing multiple objectives
- **Human-AI Partnership**: Learning from expert feedback

## Future Extensions

Potential enhancements for this demo:

- **Multi-Crop Support**: Different plant types with varying needs
- **Seasonal Cycles**: Long-term growth patterns and planning
- **Pest/Disease Management**: Reactive and preventive measures
- **Market Integration**: Optimizing for crop value and demand
- **Sustainability Metrics**: Carbon footprint and environmental impact

## Technology Stack

- **Backend**: FastAPI with WebSocket support
- **Frontend**: Vanilla JavaScript with Chart.js
- **Simulation**: Custom plant growth and environment models
- **POET Framework**: Mock implementation showcasing learning concepts

---

This demo represents the future of AI-enhanced agriculture, where intelligent systems learn to optimize crop production while minimizing resource usage and environmental impact. 