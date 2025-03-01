#!/bin/sh

# Start FastAPI in the background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to be available
until curl -s http://localhost:8000/docs > /dev/null; do
  echo "Waiting for FastAPI to start..."
  sleep 3
done

# Start Streamlit
streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.enableCORS false
