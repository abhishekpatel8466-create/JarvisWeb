FROM python:3.10-slim

# Install necessary system dependencies for Ollama and TTS
RUN apt-get update && apt-get install -y curl bash zstd

# Install Ollama Service
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set up user and permissions for Hugging Face Spaces environment
# HF Spaces run as a specialized user for security purposes
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy all the folder files into the HF Space container
COPY --chown=user . $HOME/app

# Ensure start script has executable permissions
RUN chmod +x $HOME/app/start_hf.sh

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Start the boot sequence script
CMD ["bash", "start_hf.sh"]
