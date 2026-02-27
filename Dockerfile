FROM huggingface/transformers-pytorch:latest

# Install system utilities needed for Ollama
RUN apt-get update && apt-get install -y curl wget ca-certificates && rm -rf /var/lib/apt/lists/*

# Install Ollama (binary) – works on CPU only
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (app.py, static/, templates/, etc.)
COPY . /app

# Make the start script executable and set entrypoint
RUN chmod +x start.sh
ENTRYPOINT ["./start.sh"]
