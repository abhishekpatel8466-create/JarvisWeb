FROM python:3.10-slim

# Install system utilities (minimal)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV PORT=10000

# Expose the default Render port
EXPOSE 10000

# Start the application
CMD ["python", "app.py"]
