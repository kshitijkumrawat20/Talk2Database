FROM python:3.9-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Clean pip cache and install dependencies
RUN pip cache purge && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY . .

EXPOSE 80 8000

CMD ["/bin/sh", "start.sh"]
