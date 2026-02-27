import os
import json
import uuid
import asyncio
import threading
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import edge_tts
from bs4 import BeautifulSoup
from groq import Groq

app = Flask(__name__)
CORS(app)

# Per-session memory (limited size to prevent OOM)
session_history = {}

def search_the_web(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd')
        if results:
            return results[0].get_text()[:500]
    except:
        return None
    return None

def text_to_audio(text, voice, file_path):
    if not text: return
    clean_text = text.replace("**", "").replace("*", "").replace("#", "").replace("`", "")
    
    async def generate_speech():
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(file_path)
    
    # Use a new event loop for this thread to avoid issues with the main loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(generate_speech())
    finally:
        loop.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    voice = data.get('voice', 'en-IN-PrabhatNeural')
    mode = data.get('mode', 'casual')
    use_internet = data.get('useInternet', True)
    history_mode = data.get('historyMode', 'keep')
    
    # Simple session tracking (using IP for now, not perfect but better than global)
    user_id = request.remote_addr or "guest"
    if user_id not in session_history or history_mode == "clear":
        session_history[user_id] = []

    history = session_history[user_id]
    
    # Core Personas
    MENTOR_PROMPT = """You are Jarvis, a Silicon Valley Software Architect. Professional, concise, FAANG-level insights."""
    CASUAL_PROMPT = """You are Jarvis, a cool human friend. Be natural, brief, and supportive. No academic talk."""

    def generate():
        # Update/Inject System Prompt
        base_prompt = CASUAL_PROMPT if mode == "casual" else MENTOR_PROMPT
        if not history or history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": base_prompt})
        else:
            history[0]["content"] = base_prompt

        # Search Logic
        final_prompt = question
        needs_internet = any(word in question.lower() for word in ['today', 'current', 'news', 'weather', 'latest', 'price of', 'who won', 'search'])
        if use_internet and needs_internet:
            live_data = search_the_web(question)
            if live_data:
                final_prompt = f"{question}\n\n[SYSTEM]: Live Info: {live_data}"

        history.append({'role': 'user', 'content': final_prompt})
        
        # Prune local history to last 10 messages to save memory
        if len(history) > 11:
            history[1:] = history[-10:]

        try:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                yield f"data: {json.dumps({'error': 'GROQ_API_KEY missing'})}\n\n"
                return

            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                temperature=0.4,
                stream=True
            )

            full_response = ""
            audio_triggered = False
            
            # Ensure static dir exists
            if not os.path.exists('static'): os.makedirs('static')

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Pre-cache Audio (Thread Safe)
                    if not audio_triggered and len(full_response) > 100 and any(p in full_response for p in ['. ', '! ', '? ', '\n']):
                        audio_triggered = True
                        temp_filename = f"audio_{uuid.uuid4().hex}.mp3"
                        temp_path = os.path.join("static", temp_filename)
                        threading.Thread(target=text_to_audio, args=(full_response, voice, temp_path)).start()
                    
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Final Cleanup
            history[-1]['content'] = question # Store clean question
            history.append({'role': 'assistant', 'content': full_response})
            
            # Final Full Audio
            final_filename = f"audio_{uuid.uuid4().hex}.mp3"
            final_path = os.path.join("static", final_filename)
            text_to_audio(full_response, voice, final_path) # Direct call for final
            
            yield f"data: {json.dumps({'audio': f'/static/{final_filename}'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    if not os.path.exists('static'): os.makedirs('static')
    app.run(host="0.0.0.0", port=port, debug=False)
