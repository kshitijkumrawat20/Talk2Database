#!/bin/bash

# Start the FastAPI backend server and store its PID
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a few seconds for the backend to start
sleep 5

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "Backend started successfully on port 8000"
else
    echo "Backend failed to start"
    exit 1
fi

# Start the Streamlit frontend server
streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.address 0.0.0.0