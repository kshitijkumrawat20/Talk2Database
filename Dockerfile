FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies for aws 
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev \
#     gcc \
#     g++ \
#     nginx \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . /app

# Nginx configuration
# RUN echo " \
#     server { \
#         listen 80; \
#         server_name localhost; \
#         location / { \
#             proxy_pass http://localhost:8501; \
#             proxy_set_header Host \$host; \
#             proxy_set_header X-Real-IP \$remote_addr; \
#             proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; \
#             proxy_set_header X-Forwarded-Proto \$scheme; \
#         } \
#     }" > /etc/nginx/conf.d/default.conf

# Expose the ports
# EXPOSE 8000 8501 80
# EXPOSE 8000 

# Start Nginx and then the backend and frontend
# CMD service nginx start && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & streamlit run app/frontend/Talk2SQL.py --server.address=0.0.0.0 --server.port=8501
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
