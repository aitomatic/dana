# Real-Time Credit Approval with Dana

Build a production-ready credit approval system in minutes, not months.

## Quick Start

```bash
# Install Dana
pip install dana

# Create a credit approval agent
dana create agent CreditApprovalSystem --domain=japanese_banking
```

## API Key Setup

Dana uses environment variables for API key configuration. No prompts during installation - setup happens at runtime.

### What to Expect

1. **Installation**: `pip install dana` completes without API key prompts
2. **Runtime Configuration**: Dana automatically detects API keys from environment variables

### Get Your API Key

**Recommended (Free)**: Use [Ollama](https://ollama.ai) with [Qwen2.5:7B](https://ollama.ai/library/qwen2.5) - the most popular open-source model among Japanese developers

**For Japanese Developers**: 
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Qwen2.5:7B (excellent Japanese support, free)
ollama pull qwen2.5:7b

# Set your API key to use Ollama
export DANA_API_KEY="ollama://qwen2.5:7b"
```

**Alternative Providers**: Dana supports multiple providers via environment variables:
```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Local/Ollama
export LOCAL_API_KEY="ollama://qwen2.5:7b"
```

### Verify Setup
```bash
dana --version
# Should show Dana version and confirm API key is configured
```

### Why Qwen2.5:7B?

- **Japanese Excellence**: Trained on extensive Japanese text, outperforms most models for Japanese tasks
- **Cost Effective**: Completely free to run locally
- **Developer Friendly**: Simple setup, no rate limits
- **Production Ready**: Used by major Japanese tech companies
- **Privacy**: Runs on your infrastructure, no data leaves your network

## The Code

### 1. Create the Agent

```dana
# Dana auto-generates domain-specific knowledge
dana create agent CreditApprovalSystem --domain=japanese_banking
```

This creates:
```
CreditApprovalSystem/
├── agent.na          # System coordination  
├── knowledge.na      # Banking regulations, credit models
├── workflows.na      # Decisioning process
└── resources.na      # APIs, bureaus, systems
```

### 2. Define the Pipeline

```dana
@compliance("FSA,JFSA,Basel_III")
@sla_target("< 2_seconds")
def credit_approval_pipeline = [
    ApplicationValidator,    # Validates documents
    CreditBureauQuery,      # Queries bureaus in parallel
    InternalScoring,        # Applies scoring models
    RiskAssessment,         # Basel III calculations
    FraudDetection,         # Real-time screening
    ComplianceChecker,      # Regulatory validation
    DecisionEngine          # Approve/reject with reasoning
] | audit_trail | regulatory_reporting
```

### 3. Test It

```dana
# Test with a loan application
sample_application = {
    "applicant_id": "12345",
    "requested_amount": 5000000,  # ¥5M loan
    "purpose": "home_renovation",
    "annual_income": 8000000,     # ¥8M salary
    "employment_type": "permanent",
    "documents": ["salary_slip", "bank_statement", "identity_card"]
}

decision = credit_approval_pipeline(sample_application)
print(decision)
```

### 4. See the Results

```json
{
  "decision": "APPROVED",
  "approved_amount": 5000000,
  "interest_rate": 2.8,
  "credit_score": 720,
  "risk_rating": "LOW",
  "processing_time_ms": 847,
  "compliance_status": {
    "fsa_requirements": "✓ ALL_SATISFIED",
    "basel_iii_capital_impact": "0.02% of total capital",
    "documentation_complete": "✓ ALL_DOCUMENTS_VERIFIED"
  },
  "audit_trail": "Full regulatory documentation generated"
}
```

## What Just Happened

- **Domain Knowledge**: Dana automatically knows Japanese banking regulations, credit bureaus (CIC, JICC, KSC), and FSA compliance requirements
- **Multi-Agent Orchestration**: 7 specialized agents work in parallel with automatic error handling and data flow
- **Compliance Built-in**: Regulatory validation, audit trails, and reporting happen automatically
- **Production Performance**: Sub-second processing with enterprise SLAs
- **Edge Case Handling**: Rejections include compliant reasoning and alternative offers

## Try Edge Cases

```dana
problematic_application = {
    "applicant_id": "99999",
    "requested_amount": 50000000,  # ¥50M - high risk
    "annual_income": 3000000,      # Low income
    "employment_type": "contract",  # Non-permanent
    "credit_history": "no_history" # First-time borrower
}

decision2 = credit_approval_pipeline(problematic_application)
```

Result:
```json
{
  "decision": "REJECTED",
  "rejection_reason": "Debt-to-income ratio exceeds FSA limits (16.7x vs max 10x)",
  "alternative_offer": {
    "approved_amount": 2500000,
    "interest_rate": 4.2,
    "conditions": ["Require co-signer", "6-month probation period"]
  },
  "regulatory_compliance": "✓ Rejection follows FSA fair lending practices"
}
```

## Key Features

- **Domain Expertise**: Pre-loaded with industry-specific knowledge
- **Regulatory Compliance**: Built-in validation and audit trails  
- **Production Performance**: Sub-second processing with SLAs
- **Automatic Orchestration**: Complex workflows in declarative syntax
- **Self-Improving**: Systems learn and optimize over time

## Next Steps

1. **Run This Example**: Execute the code above
2. **Customize for Your Domain**: `dana create agent YourSystem --domain=your_industry`
3. **Scale to Production**: Deploy with confidence - compliance and performance are built-in

---

*Transform complex enterprise AI challenges into simple, declarative solutions that are production-ready from day one.*
