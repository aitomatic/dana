# Maritime Navigation System - Usage Guide

## 🚀 **Quick Start**

### **Option 1: Use Default Scenario (Recommended)**

```bash
./run-maritime-navigation
```

- Uses the pre-configured scenario in `.input/scenario.json`
- No parameters needed
- Perfect for testing and demonstration

### **Option 2: Use Different Scenario Files**

```bash
uv run dana maritime_navigation.na scenario="$(cat .input/crossing-scenario.txt)"
uv run dana maritime_navigation.na scenario="$(cat .input/overtaking-scenario.txt)"
```

## 📝 **How to Change Scenarios**

### **Method 1: Edit Text File (Easiest)**

1. Open `.input/scenario.txt`
2. Modify the vessel information:
   - Vessel IDs
   - Positions (latitude/longitude)
   - Courses (degrees)
   - Speeds (knots)
3. Save the file
4. Run: `./run-maritime-navigation`

### **Method 2: Use Pre-made Scenario Files**

1. Use existing scenario files:
   - `.input/scenario.txt` - Head-on collision (default)
   - `.input/crossing-scenario.txt` - Crossing situation
   - `.input/overtaking-scenario.txt` - Overtaking scenario
2. Run with: `uv run dana maritime_navigation.na scenario="$(cat .input/crossing-scenario.txt)"`

## 🎯 **Example Scenarios**

### **Head-on Collision (Current)**

- Vessel A: 090° at 20 knots
- Vessel B: 270° at 18 knots
- Result: High risk head-on situation

### **Crossing Situation**

- Vessel A: 000° at 15 knots
- Vessel B: 090° at 25 knots
- Result: Crossing with Vessel B on starboard

### **Overtaking**

- Vessel A: 090° at 22 knots
- Vessel B: 090° at 16 knots
- Result: Vessel A overtaking Vessel B

## 📁 **File Structure**

```
Maritime-Navigation/
├── run-maritime-navigation          # Unix/Linux run script
├── run-maritime-navigation.bat      # Windows run script
├── maritime_navigation.na           # Main analysis script
├── .input/
│   ├── scenario.txt                   # Default scenario (head-on)
│   ├── crossing-scenario.txt          # Crossing situation
│   └── overtaking-scenario.txt        # Overtaking scenario
├── .output/                         # Analysis results
└── resources/                       # Knowledge databases
```

## 🔧 **Troubleshooting**

### **System Won't Run**

- Ensure you're in the Maritime-Navigation directory
- Check that `uv` is installed and working
- Verify Dana language is properly set up

### **Incomplete Output**

- Check that all resource files exist in `resources/` directory
- Ensure input file has proper formatting
- Look for syntax errors in the main script

### **Different Results**

- Clear `.cache/` directory to reset RAG indices
- Check that input parameters are correctly formatted
- Verify vessel IDs match those in `vessel_registry.txt`

## 📊 **Output Files**

- `navigation-recommendation.txt` - Complete analysis report
- `step-1.txt` through `step-4.txt` - Individual step results
- All files are saved in `.output/` directory

## 🎉 **Success Indicators**

- System runs without errors
- All 4 analysis steps complete
- Final recommendations show proper course and speed actions
- Output files are generated in `.output/` directory
