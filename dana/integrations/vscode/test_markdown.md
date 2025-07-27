# Dana Syntax Highlighting Test

This is a test of Dana syntax highlighting in markdown preview.

## Basic Dana Code

```dana
# Basic knowledge curation
context = {"domain": "general", "task": "knowledge_extraction"}
sources = ["./docs/api.md", "./docs/architecture.md"]
ecosystem = curate_knowledge_ecosystem(context, sources)
```

## Dana Functions

```dana
def analyze_defects(process_data: dict, equipment_logs: list) -> dict:
    """Analyze semiconductor defects from process data."""
    
    results = {
        "defect_count": 0,
        "critical_defects": [],
        "recommendations": []
    }
    
    for log in equipment_logs:
        if log.get("defect_detected", False):
            results["defect_count"] += 1
            
            if log["severity"] == "critical":
                results["critical_defects"].append(log)
    
    return results
```

## Dana Structs

```dana
struct DefectAnalysis:
    """Structure for defect analysis results."""
    
    public: defect_count: int
    public: critical_defects: list
    public: recommendations: list
    
    def __init__(self):
        self.defect_count = 0
        self.critical_defects = []
        self.recommendations = []
```

## Test Results

The highlighting should work automatically in the markdown preview. If you see this text, the markdown is rendering correctly.

### Expected Behavior

- Comments should be green
- Keywords should be blue
- Strings should be orange
- Numbers should be light green
- Functions should be yellow
- Types should be teal 