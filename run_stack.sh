#!/bin/bash
# Start script for the Generic AI Copilot
echo "🚀 Starting Generic RAG Backend & Frontend..."

# Ensure dependencies are installed
# pip install -r requirements.txt

export PYTHONPATH=$PYTHONPATH:.

# The backend startup automatically spawns the Streamlit frontend as a sidecar process
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
