---
title: Jarvis IIT Professor
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Professor Jarvis - AI Buddy

This is the Hugging Face Spaces deployment for Professor Jarvis, a locally-hosted AI Mentor built with Ollama, Flask, and Edge-TTS.

## How it works
This space uses a custom `Dockerfile` to setup a Linux environment that installs and runs the Ollama background service alongside a Flask web server on port 7860. It automatically downloads a quantized model and applies the custom `IIT_Professor.Modelfile` persona before starting up!
