FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any are needed (e.g. build-essential, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run FastAPI app with uvicorn
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
