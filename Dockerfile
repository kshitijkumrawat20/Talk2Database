FROM python:3.9-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Disable pip cache and force reinstall
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

# Copy the application code
COPY . .

EXPOSE 80 8000

CMD ["/bin/sh", "start.sh"]
