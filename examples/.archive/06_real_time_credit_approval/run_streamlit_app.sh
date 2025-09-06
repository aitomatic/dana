#!/bin/bash

# Run the SMBC Credit Approval System Streamlit App
echo "🏦 Starting SMBC Credit Approval System..."
echo "📊 Loading Dana agent and UCI dataset..."
echo "🌐 Opening web interface..."

# Run Streamlit app
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 