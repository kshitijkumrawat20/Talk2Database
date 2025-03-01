#!/bin/bash

# Start the FastAPI backend server and wait for it to be ready
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Wait for FastAPI to start (give it 5 seconds)
sleep 5

# Start the Streamlit frontend server
streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.address 0.0.0.0

# If Streamlit exits, kill FastAPI
kill $FASTAPI_PID