#!/bin/bash

# Start the FastAPI backend server and wait for it to be ready
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit frontend server
streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.enableCORS false