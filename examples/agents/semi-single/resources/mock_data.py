"""
Mock semiconductor test data for yield analysis demos.

This module provides realistic wafer test data with interesting failure patterns
that demonstrate the value of deterministic vs probabilistic yield analysis.
"""

# Realistic wafer test results with interesting patterns
WAFER_TEST_DATA = {
    "wafer_id": "W12345-789",
    "product": "CPU_7nm_A53_HiPerf",
    "test_date": "2025-01-15",
    "total_dies": 1000,
    "good_dies": 685,
    "yield_percent": 68.5,
    # Failure bins with interesting patterns for analysis
    "failure_bins": {
        "BIN_1": {
            "count": 180,
            "description": "SRAM bit failures",
            "test_type": "memory",
            "failure_mode": "stuck_bits",
            "spatial_pattern": "clustered",  # Systematic - process issue
            "notes": "Pattern shows edge die clustering, suggests process sensitivity",
        },
        "BIN_2": {
            "count": 75,
            "description": "Logic path timing violations",
            "test_type": "timing",
            "failure_mode": "slow_path",
            "spatial_pattern": "random",  # Random - design margin issue
            "notes": "Randomly distributed, marginal timing design",
        },
        "BIN_3": {
            "count": 35,
            "description": "I/O buffer failures",
            "test_type": "io",
            "failure_mode": "driver_weak",
            "spatial_pattern": "systematic",  # Systematic - package issue
            "notes": "Peripheral dies only, package-related stress",
        },
        "BIN_4": {
            "count": 15,
            "description": "Voltage regulator instability",
            "test_type": "power",
            "failure_mode": "vdd_dropout",
            "spatial_pattern": "random",
            "notes": "Low volume, random distribution",
        },
        "BIN_5": {
            "count": 8,
            "description": "Leakage current excessive",
            "test_type": "leakage",
            "failure_mode": "high_iddq",
            "spatial_pattern": "random",
            "notes": "Very low volume, process outliers",
        },
        "BIN_6": {
            "count": 2,
            "description": "Functional logic errors",
            "test_type": "functional",
            "failure_mode": "logic_fail",
            "spatial_pattern": "isolated",
            "notes": "Rare, likely random defects",
        },
    },
    # Product business context
    "product_context": {
        "average_selling_price_usd": 150,  # ASP per die
        "monthly_volume_wafers": 10000,
        "customer_tier": "Tier-1 datacenter",
        "revenue_criticality": "HIGH",
        "quality_requirements": "Automotive grade (zero defects)",
    },
    # Wafer manufacturing context
    "manufacturing_context": {
        "fab": "Fab 5",
        "process_node": "7nm FinFET",
        "process_flow": "1274 steps",
        "cycle_time_days": 45,
        "wafer_cost_usd": 5000,
    },
}

# Historical yield trend data for correlation
HISTORICAL_YIELD_DATA = {
    "product": "CPU_7nm_A53_HiPerf",
    "weeks": [
        {"week": "2025-W01", "yield": 68.5, "volume": 2500},
        {"week": "2024-W52", "yield": 68.2, "volume": 2400},
        {"week": "2024-W51", "yield": 67.8, "volume": 2450},
        {"week": "2024-W50", "yield": 72.1, "volume": 2300},  # Better yield before process change
        {"week": "2024-W49", "yield": 71.8, "volume": 2350},
        {"week": "2024-W48", "yield": 71.5, "volume": 2300},
        {"week": "2024-W47", "yield": 71.2, "volume": 2250},
        {"week": "2024-W46", "yield": 70.9, "volume": 2200},
        {"week": "2024-W45", "yield": 70.5, "volume": 2150},
        {"week": "2024-W44", "yield": 70.2, "volume": 2100},
        {"week": "2024-W43", "yield": 69.8, "volume": 2050},
        {"week": "2024-W42", "yield": 69.5, "volume": 2000},
    ],
    "trend": "degrading",
    "trend_analysis": "Yield degraded ~4% since week 50 (early December). Coincides with etch recipe optimization for throughput.",
    "process_changes": [
        {
            "week": "2024-W50",
            "change": "Metal etch recipe: Increased RF power 5% for throughput improvement",
            "impact": "Suspected cause of SRAM yield loss - more aggressive etch may damage cell structures",
        }
    ],
}

# Historical similar failure cases for correlation
HISTORICAL_FAILURE_CASES = [
    {
        "case_id": "YLD-2023-087",
        "date": "2023-08-15",
        "product": "CPU_7nm_A53_Standard",
        "primary_bin": "BIN_1 (SRAM failures)",
        "root_cause": "Metal etch over-etch causing SRAM cell damage",
        "failure_count": 195,
        "yield_impact": "-5.2%",
        "resolution": "Reduced etch RF power by 8%, adjusted etch time",
        "time_to_resolve_days": 12,
        "revenue_recovered_usd": 15000000,
        "similarity_score": 0.92,  # Very similar to current issue
        "notes": "Nearly identical failure pattern. Resolution: etch recipe tuning.",
    },
    {
        "case_id": "YLD-2024-034",
        "date": "2024-03-22",
        "product": "CPU_7nm_A53_HiPerf",
        "primary_bin": "BIN_3 (I/O failures)",
        "root_cause": "Package substrate warpage during assembly",
        "failure_count": 45,
        "yield_impact": "-1.8%",
        "resolution": "Adjusted assembly temperature profile, changed substrate supplier",
        "time_to_resolve_days": 18,
        "revenue_recovered_usd": 5000000,
        "similarity_score": 0.65,
        "notes": "I/O failures, but different root cause (package vs die-level)",
    },
    {
        "case_id": "YLD-2024-091",
        "date": "2024-11-05",
        "product": "GPU_7nm_G100",
        "primary_bin": "BIN_2 (Timing violations)",
        "root_cause": "Design marginality, insufficient timing margin",
        "failure_count": 85,
        "yield_impact": "-3.1%",
        "resolution": "Design rev to add timing margin (long-term), voltage screening (short-term)",
        "time_to_resolve_days": 90,  # Design fix takes long time
        "revenue_recovered_usd": 8000000,
        "similarity_score": 0.45,
        "notes": "Timing failures, but design-limited (hard to fix)",
    },
]

# Bin details for analysis
BIN_DETAILS = {
    "BIN_1": {
        "test_conditions": "DC parametric, SRAM array test @ nominal voltage",
        "failure_mechanism": "Bit cells stuck at 0 or 1, read/write failures",
        "design_info": "32KB L1 cache, 6T SRAM cells",
        "typical_root_causes": [
            "Etch damage to cell transistors",
            "Implant dose variation",
            "Contact resistance issues",
            "Cell ratio imbalance",
        ],
        "fix_difficulty": "MEDIUM",  # Process tuning typically feasible
        "fix_difficulty_reasoning": "SRAM failures often process-related. Recipe tuning or implant adjustment can resolve. Not design-limited.",
        "typical_time_to_fix_days": "10-20 days",
    },
    "BIN_2": {
        "test_conditions": "At-speed functional test @ nominal voltage and frequency",
        "failure_mechanism": "Critical paths fail timing at target frequency",
        "design_info": "Complex logic paths, long interconnect",
        "typical_root_causes": [
            "Marginal timing design",
            "Process variation (interconnect RC)",
            "Voltage droop",
            "Temperature sensitivity",
        ],
        "fix_difficulty": "HARD",  # Often design-limited
        "fix_difficulty_reasoning": "Timing failures often require design changes (long cycle time). Process fixes limited. May need voltage screening or frequency binning.",
        "typical_time_to_fix_days": "60-90 days (design rev)",
    },
    "BIN_3": {
        "test_conditions": "I/O buffer DC and AC tests",
        "failure_mechanism": "Drive strength insufficient, signal integrity issues",
        "design_info": "High-speed I/O buffers, 112 I/O pads",
        "typical_root_causes": [
            "Package-induced stress",
            "Interconnect resistance",
            "ESD protection device variation",
            "Assembly process issues",
        ],
        "fix_difficulty": "MEDIUM",  # Package or assembly process
        "fix_difficulty_reasoning": "I/O failures often package or assembly related. Can adjust assembly process, change substrate, or screen at package test.",
        "typical_time_to_fix_days": "15-30 days",
    },
    "BIN_4": {
        "test_conditions": "Power supply regulation test under load transients",
        "failure_mechanism": "Voltage regulator oscillation or dropout",
        "design_info": "On-die LDO regulators, decoupling capacitors",
        "typical_root_causes": [
            "Decap density insufficient",
            "Regulator loop instability",
            "Metal resistance variation",
            "Design marginality",
        ],
        "fix_difficulty": "MEDIUM-HARD",  # May need design change
        "fix_difficulty_reasoning": "May require design changes to add decaps or adjust regulator. Process fixes limited.",
        "typical_time_to_fix_days": "30-60 days",
    },
    "BIN_5": {
        "test_conditions": "Quiescent current (IDDQ) test",
        "failure_mechanism": "Excessive leakage current",
        "design_info": "Bulk leakage across all transistors",
        "typical_root_causes": ["Gate oxide defects", "Junction leakage", "ESD damage", "Contamination"],
        "fix_difficulty": "HARD",  # Often random defects
        "fix_difficulty_reasoning": "Leakage often random defects or contamination. Difficult to systematically improve. May need defect density reduction (long-term).",
        "typical_time_to_fix_days": "45-90 days",
    },
    "BIN_6": {
        "test_conditions": "Full functional test vectors",
        "failure_mechanism": "Logic function incorrect",
        "design_info": "Complex state machines, arithmetic units",
        "typical_root_causes": ["Random defects (shorts, opens)", "Rare design bugs", "Exotic failure modes"],
        "fix_difficulty": "HARD",  # Often random or design bugs
        "fix_difficulty_reasoning": "Functional errors typically random defects (hard to improve yield) or rare design bugs (need design fix).",
        "typical_time_to_fix_days": "60-120 days",
    },
}


def get_wafer_test_data():
    """Get mock wafer test results."""
    return WAFER_TEST_DATA


def get_historical_yield_data(product, weeks=12):
    """Get historical yield trend data."""
    return {
        "product": product,
        "weeks": HISTORICAL_YIELD_DATA["weeks"][:weeks],
        "trend": HISTORICAL_YIELD_DATA["trend"],
        "trend_analysis": HISTORICAL_YIELD_DATA["trend_analysis"],
        "process_changes": HISTORICAL_YIELD_DATA["process_changes"],
    }


def get_similar_failure_cases(bin_id):
    """Get historical similar failure cases."""
    # Filter cases relevant to the bin
    if bin_id == "BIN_1":
        # SRAM failures - very similar case exists
        return [HISTORICAL_FAILURE_CASES[0]]
    elif bin_id == "BIN_3":
        # I/O failures - somewhat similar case
        return [HISTORICAL_FAILURE_CASES[1]]
    elif bin_id == "BIN_2":
        # Timing failures - less similar case
        return [HISTORICAL_FAILURE_CASES[2]]
    else:
        return []


def get_bin_details(bin_id):
    """Get detailed bin information."""
    return BIN_DETAILS.get(bin_id, {})
