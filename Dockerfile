FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . /app

# Install the application as a package
RUN pip install --no-cache-dir .

# Expose the ports
EXPOSE 8000 8501

# Command to run the backend and frontend
CMD uvicorn talk2sql.app.main:app --host 0.0.0.0 --port 8000 --reload & streamlit run /app/app/frontend/Talk2SQL.py --server.address=0.0.0.0 --server.port=8501