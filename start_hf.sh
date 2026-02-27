#!/bin/bash

# Start Ollama service in the background
echo "Starting Ollama Server..."
ollama serve &

# Wait for Ollama to boot
sleep 10

# Read the base model name from the first line of IIT_Professor.Modelfile
# e.g., "FROM qwen2.5:1.5b" -> will pull "qwen2.5:1.5b"
BASE_MODEL=$(head -n 1 IIT_Professor.Modelfile | awk '{print $2}')
echo "Jarvis is configured to use base model: $BASE_MODEL"

# Pull the base model required by the user's config
echo "Downloading Base Brain (This may take a few minutes if not cached)..."
ollama pull $BASE_MODEL

# Build the JarvisTeacher persona inside Ollama
echo "Compiling JarvisTeacher Persona..."
ollama create JarvisTeacher -f IIT_Professor.Modelfile

# Start the Flask app
echo "Starting the Web Dashboard..."
export PORT=7860
python app.py
