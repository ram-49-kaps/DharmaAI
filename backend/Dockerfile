# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements file first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Hugging Face Spaces expects the app to bind to 0.0.0.0:7860 by default
# But FastAPI/Uvicorn can bind to 8000 and we can configure HF or just let it port map
# We will use 7860 as it's the default Hugging Face space port.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
