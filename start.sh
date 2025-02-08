#!/bin/bash

# Start the FastAPI backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit frontend server
streamlit run app/frontend/frontend_app.py --server.port 80 --server.enableCORS false