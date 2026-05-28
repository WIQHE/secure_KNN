FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt httpx sqlalchemy psycopg2-binary python-multipart

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
