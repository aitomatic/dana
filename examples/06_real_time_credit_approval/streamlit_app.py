#!/usr/bin/env python3
"""
SMBC Credit Approval System - Streamlit Web Interface
Real-time credit decisioning with Dana agent integration
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="SMBC Credit Approval System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional banking interface
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .decision-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .decision-approved {
        background: #d4edda;
        border-left-color: #28a745;
    }
    
    .decision-conditional {
        background: #fff3cd;
        border-left-color: #ffc107;
    }
    
    .decision-rejected {
        background: #f8d7da;
        border-left-color: #dc3545;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .chat-user {
        background: #e3f2fd;
        border-left-color: #2196f3;
        margin-left: 2rem;
    }
    
    .chat-agent {
        background: #f3e5f5;
        border-left-color: #9c27b0;
        margin-right: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .quick-action-btn {
        background: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.25rem;
        cursor: pointer;
    }
    
    .quick-action-btn:hover {
        background: #0056b3;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_application' not in st.session_state:
    st.session_state.current_application = None
if 'dana_agent' not in st.session_state:
    st.session_state.dana_agent = None

def load_uci_dataset() -> pd.DataFrame:
    """Load UCI credit dataset from crx.data file"""
    try:
        # Define column names for UCI dataset
        columns = [
            'checking_status', 'duration', 'credit_history', 'purpose', 
            'credit_amount', 'savings_status', 'employment', 'installment_commitment',
            'personal_status', 'other_parties', 'residence_since', 'property_magnitude',
            'age', 'other_payment_plans', 'housing', 'existing_credits',
            'job', 'num_dependents', 'own_telephone', 'foreign_worker', 'class'
        ]
        
        # Load the dataset
        df = pd.read_csv('credit+approval/crx.data', header=None, names=columns)
        return df
    except Exception as e:
        st.error(f"❌ Error loading UCI dataset: {e}")
        return pd.DataFrame()

def load_uci_case(case_number: int) -> Dict[str, Any]:
    """Load a specific case from UCI dataset and format as application"""
    df = load_uci_dataset()
    
    if df.empty or case_number < 1 or case_number > len(df):
        return {}
    
    # Get the case (subtract 1 for 0-based indexing)
    case = df.iloc[case_number - 1]
    
    # Map UCI data to application format with safe parsing
    def safe_int(value, default=0):
        try:
            if value == '?' or value == '':
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    application = {
        "applicant_id": f"UCI-{case_number:03d}",
        "name": f"Applicant {case_number}",
        "age": safe_int(case['age'], 35),
        "employment_type": "permanent" if case['employment'] in ['a', 'b'] else "contract",
        "employment_years": safe_int(case['employment'], 3),
        "annual_income": safe_int(case['credit_amount'], 50000000) * 1000,  # Convert to yen
        "existing_debt": safe_int(case['existing_credits'], 2) * 500000,  # Estimate
        "credit_history": case['credit_history'],
        "requested_amount": safe_int(case['credit_amount'], 30000000) * 800,  # 80% of credit amount
        "loan_purpose": case['purpose'],
        "checking_status": case['checking_status'],
        "savings_status": case['savings_status'],
        "housing": case['housing'],
        "job": case['job'],
        "class": case['class']
    }
    
    return application

def initialize_dana_agent():
    """Initialize the Dana credit approval agent"""
    try:
        from dana.core import DanaInterpreter
        import os
        
        # Create a Dana interpreter
        interpreter = DanaInterpreter()
        
        # Load the agent files
        agent_file = "agent.na"
        knowledge_file = "knowledge.na"
        workflows_file = "workflows.na"
        resources_file = "resources.na"
        
        # Check if files exist
        if not all(os.path.exists(f) for f in [agent_file, knowledge_file, workflows_file, resources_file]):
            st.warning("⚠️ Some Dana agent files are missing")
            return None
        
        # Load and execute the agent files
        try:
            with open(agent_file, 'r') as f:
                agent_code = f.read()
            
            with open(knowledge_file, 'r') as f:
                knowledge_code = f.read()
            
            with open(workflows_file, 'r') as f:
                workflows_code = f.read()
            
            with open(resources_file, 'r') as f:
                resources_code = f.read()
            
            # Execute the code to register the agent
            interpreter.execute(agent_code)
            interpreter.execute(knowledge_code)
            interpreter.execute(workflows_code)
            interpreter.execute(resources_code)
            
            # Return the interpreter for now
            return interpreter
            
        except Exception as e:
            st.error(f"❌ Error loading Dana files: {e}")
            return None
        
    except ImportError:
        st.warning("⚠️ Dana package not found. Install with: pip install dana")
        return None
    except Exception as e:
        st.error(f"❌ Error initializing Dana agent: {e}")
        return None

def create_mock_agent():
    """Create a mock agent for demonstration when Dana is not available"""
    class MockAgent:
        def execute(self, task):
            if "credit" in task.lower():
                return "APPROVED - Credit application processed successfully"
            elif "risk" in task.lower():
                return "Risk factors analyzed: Income stability, employment history, credit score"
            elif "compliance" in task.lower():
                return "Compliance check passed: FSA, Basel III, fair lending requirements met"
            else:
                return "Dana agent response: " + task
    
    return MockAgent()

def process_application(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process application through Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return {"error": "Dana agent not available"}
        
        # Convert application data to task string
        task = f"Process credit application: {json.dumps(app_data)}"
        
        # Use the interpreter to execute the task
        result = st.session_state.dana_agent.execute(task)
        
        # Try to parse result as JSON, otherwise return as string
        try:
            return json.loads(str(result))
        except (json.JSONDecodeError, TypeError):
            return {"decision": "PENDING", "reason": str(result), "engine": "dana"}
            
    except Exception as e:
        st.error(f"❌ Error processing application: {e}")
        return {"error": str(e)}

def chat_with_dana(user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Chat with Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return "Sorry, the Dana agent is not available at the moment."
        
        # Add context to the message if provided
        if context:
            full_message = f"{user_message}\n\nContext: {json.dumps(context)}"
        else:
            full_message = user_message
        
        # Use the interpreter to execute the message
        response = st.session_state.dana_agent.execute(full_message)
        return str(response)
    except Exception as e:
        return f"Error communicating with Dana agent: {e}"

def analyze_application(app_data: Dict[str, Any]) -> str:
    """Analyze application using Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return "Dana agent not available"
        
        # Create analysis task
        task = f"Analyze credit risk for application: {json.dumps(app_data)}"
        result = st.session_state.dana_agent.execute(task)
        return str(result)
    except Exception as e:
        return f"Error analyzing application: {e}"

def check_risk_factors(app_data: Dict[str, Any]) -> str:
    """Check risk factors using Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return "Dana agent not available"
        
        # Use Dana agent to analyze risk factors
        task = f"Analyze and identify risk factors for this credit application: {json.dumps(app_data)}"
        result = st.session_state.dana_agent.execute(task)
        return str(result)
    except Exception as e:
        return f"Error checking risk factors: {e}"

def check_compliance(app_data: Dict[str, Any]) -> str:
    """Check compliance using Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return "Dana agent not available"
        
        # Use Dana agent to check compliance
        task = f"Check FSA, Basel III, and fair lending compliance for this application: {json.dumps(app_data)}"
        result = st.session_state.dana_agent.execute(task)
        return str(result)
    except Exception as e:
        return f"Error checking compliance: {e}"

def explain_decision(app_data: Dict[str, Any]) -> str:
    """Explain decision using Dana agent"""
    try:
        if st.session_state.dana_agent is None:
            st.session_state.dana_agent = initialize_dana_agent()
        
        if st.session_state.dana_agent is None:
            return "Dana agent not available"
        
        # Use Dana agent to explain the decision
        task = f"Explain the credit decision and reasoning in detail for this application: {json.dumps(app_data)}"
        result = st.session_state.dana_agent.execute(task)
        return str(result)
    except Exception as e:
        return f"Error explaining decision: {e}"

def display_application_form():
    """Display the application form"""
    st.subheader("📋 Credit Application Form")
    
    with st.form("credit_application"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", value="")
            age = st.number_input("Age", min_value=18, max_value=80, value=35)
            employment_type = st.selectbox(
                "Employment Type",
                ["permanent", "contract", "temporary", "self-employed"]
            )
            employment_years = st.number_input(
                "Years of Employment", 
                min_value=0, 
                max_value=50, 
                value=5
            )
            annual_income = st.number_input(
                "Annual Income (¥)", 
                min_value=1000000, 
                max_value=100000000, 
                value=50000000,
                step=1000000
            )
        
        with col2:
            existing_debt = st.number_input(
                "Existing Debt (¥)", 
                min_value=0, 
                max_value=50000000, 
                value=5000000,
                step=100000
            )
            credit_history = st.selectbox(
                "Credit History",
                ["excellent", "good", "fair", "poor", "none"]
            )
            requested_amount = st.number_input(
                "Requested Loan Amount (¥)", 
                min_value=1000000, 
                max_value=100000000, 
                value=30000000,
                step=1000000
            )
            loan_purpose = st.selectbox(
                "Loan Purpose",
                ["home_purchase", "business", "education", "debt_consolidation", "other"]
            )
        
        submitted = st.form_submit_button("🚀 Process Application")
        
        if submitted:
            application = {
                "applicant_id": f"WEB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": name,
                "age": age,
                "employment_type": employment_type,
                "employment_years": employment_years,
                "annual_income": annual_income,
                "existing_debt": existing_debt,
                "credit_history": credit_history,
                "requested_amount": requested_amount,
                "loan_purpose": loan_purpose,
                "documents": ["salary_slip", "bank_statement", "identity_document"]
            }
            
            st.session_state.current_application = application
            return application
    
    return None

def display_decision_summary(result: Dict[str, Any], app: Dict[str, Any]):
    """Display decision summary"""
    st.subheader("📊 Decision Summary")
    
    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
        return
    
    # Determine decision class for styling
    decision = result.get("decision", "PENDING").upper()
    if "APPROVED" in decision:
        decision_class = "decision-approved"
        decision_icon = "✅"
    elif "CONDITIONAL" in decision or "PENDING" in decision:
        decision_class = "decision-conditional"
        decision_icon = "⚠️"
    else:
        decision_class = "decision-rejected"
        decision_icon = "❌"
    
    # Display decision card
    st.markdown(f"""
    <div class="decision-card {decision_class}">
        <h3>{decision_icon} {decision}</h3>
        <p><strong>Reason:</strong> {result.get('reason', 'No reason provided')}</p>
        <p><strong>Approved Amount:</strong> ¥{result.get('approved_amount', 0):,}</p>
        <p><strong>Interest Rate:</strong> {result.get('interest_rate', 0):.2f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Credit Score", result.get("score", "N/A"))
    
    with col2:
        st.metric("DTI Ratio", f"{result.get('dti_ratio', 0):.1f}%")
    
    with col3:
        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")

def display_chat_interface():
    """Display the Dana agent chat interface"""
    st.subheader("💬 Dana Agent Chat")
    
    # Quick action buttons
    st.markdown("**Quick Actions:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Analyze Application", key="analyze_btn"):
            if st.session_state.current_application:
                response = analyze_application(st.session_state.current_application)
                st.session_state.chat_history.append({
                    "user": "Analyze Application",
                    "agent": response,
                    "timestamp": datetime.now()
                })
    
    with col2:
        if st.button("⚠️ Risk Factors", key="risk_btn"):
            if st.session_state.current_application:
                response = check_risk_factors(st.session_state.current_application)
                st.session_state.chat_history.append({
                    "user": "Check Risk Factors",
                    "agent": response,
                    "timestamp": datetime.now()
                })
    
    with col3:
        if st.button("📋 Compliance Check", key="compliance_btn"):
            if st.session_state.current_application:
                response = check_compliance(st.session_state.current_application)
                st.session_state.chat_history.append({
                    "user": "Check Compliance",
                    "agent": response,
                    "timestamp": datetime.now()
                })
    
    with col4:
        if st.button("💡 Explain Decision", key="explain_btn"):
            if st.session_state.current_application:
                response = explain_decision(st.session_state.current_application)
                st.session_state.chat_history.append({
                    "user": "Explain Decision",
                    "agent": response,
                    "timestamp": datetime.now()
                })
    
    # Chat input
    user_message = st.text_area("💬 Ask Dana Agent:", height=100)
    
    if st.button("Send Message", key="send_btn"):
        if user_message.strip():
            # Add user message to chat history
            st.session_state.chat_history.append({
                "user": user_message,
                "agent": "",
                "timestamp": datetime.now()
            })
            
            # Get agent response
            context = st.session_state.current_application if st.session_state.current_application else {}
            agent_response = chat_with_dana(user_message, context)
            
            # Update the last message with agent response
            if st.session_state.chat_history:
                st.session_state.chat_history[-1]["agent"] = agent_response
    
    # Display chat history
    st.subheader("📝 Chat History")
    for i, message in enumerate(st.session_state.chat_history):
        if message["user"]:
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>You:</strong> {message["user"]}
            </div>
            """, unsafe_allow_html=True)
        
        if message["agent"]:
            st.markdown(f"""
            <div class="chat-message chat-agent">
                <strong>Dana Agent:</strong> {message["agent"]}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"<small><em>{message['timestamp'].strftime('%H:%M:%S')}</em></small>", unsafe_allow_html=True)
        st.markdown("---")

def main():
    """Main application"""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏦 SMBC Credit Approval System</h1>
        <p>Real-time credit decisioning powered by Dana AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize Dana agent
    if st.session_state.dana_agent is None:
        with st.spinner("Initializing Dana agent..."):
            dana_agent = initialize_dana_agent()
            if dana_agent is None:
                st.warning("⚠️ Using mock agent for demonstration")
                st.session_state.dana_agent = create_mock_agent()
            else:
                st.session_state.dana_agent = dana_agent
    
    # Create two-column layout
    col1, col2 = st.columns([6, 4])
    
    with col1:
        # Left column - Application processing
        st.markdown("### 📊 UCI Dataset Loader")
        
        # UCI dataset loader
        case_number = st.number_input(
            "Load UCI Case (1-690):", 
            min_value=1, 
            max_value=690, 
            value=1
        )
        
        if st.button("📂 Load Case"):
            application = load_uci_case(case_number)
            if application:
                st.session_state.current_application = application
                st.success(f"✅ Loaded case {case_number}")
                st.json(application)
            else:
                st.error("❌ Invalid case number")
        
        st.markdown("---")
        
        # Application form
        application = display_application_form()
        
        # Process application
        if st.session_state.current_application:
            if st.button("🚀 Process Application", key="process_btn"):
                with st.spinner("Processing application with Dana agent..."):
                    result = process_application(st.session_state.current_application)
                    st.session_state.current_result = result
                
                # Display decision summary
                if hasattr(st.session_state, 'current_result'):
                    display_decision_summary(st.session_state.current_result, st.session_state.current_application)
    
    with col2:
        # Right column - Dana agent chat
        display_chat_interface()

if __name__ == "__main__":
    main() 