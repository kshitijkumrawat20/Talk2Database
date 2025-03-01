#!/bin/sh

# Start FastAPI in the background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit
streamlit run app/frontend/Talk2SQL.py --server.port 80 --server.enableCORS false
