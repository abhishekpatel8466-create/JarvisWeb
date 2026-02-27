FROM python:3.10-slim

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

# Bake the model into the image:
# Start the server in background, wait, then pull and create custom model
RUN nohup bash -c "ollama serve &" && \
    sleep 5 && \
    ollama pull gemma2:2b-q4_k_m && \
    ollama create JarvisTeacher -f /app/IIT_Professor.Modelfile

# Make the start script executable and set entrypoint
RUN chmod +x start.sh
ENTRYPOINT ["./start.sh"]
