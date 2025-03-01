#!/bin/bash

if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "Starting backend service..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Starting frontend service..."
    streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.address 0.0.0.0
fi