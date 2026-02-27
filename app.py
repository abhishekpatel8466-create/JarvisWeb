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

# Load context from a persistent JSON file so Jarvis "remembers" you
MEMORY_FILE = 'Jarvis_Memory.json'

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory():
    with open(MEMORY_FILE, 'w') as f:
        json.dump(chat_history, f)

chat_history = load_memory()

def search_the_web(query):
    # Same search logic as before
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

def text_to_audio(text, voice):
    # Strip markdown for cleaner audio
    if not text: return ""
    clean_text = text.replace("**", "").replace("*", "").replace("#", "").replace("`", "")
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    file_path = os.path.join("static", filename)
    
    async def generate_speech():
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(file_path)
    
    asyncio.run(generate_speech())
    return filename

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history
    data = request.json
    question = data.get('question', '')
    voice = data.get('voice', 'en-IN-PrabhatNeural')
    mode = data.get('mode', 'casual')
    use_internet = data.get('useInternet', True)
    history_mode = data.get('historyMode', 'keep')

    if history_mode == "clear":
        chat_history = []
        save_memory()

    needs_internet = any(word in question.lower() for word in ['today', 'current', 'news', 'weather', 'latest', 'price of', 'who won', 'search'])
    prompt = question

    # Define separate core personas
    MENTOR_PROMPT = """You are Jarvis, a world-class Senior Software Architect. Professional, concise, FAANG-level insights."""
    CASUAL_PROMPT = """You are Jarvis, a supportive human friend. Be natural, brief, and cool. No robot talk."""

    def generate():
        global chat_history
        
        # Determine Persona
        base_prompt = CASUAL_PROMPT if mode == "casual" else MENTOR_PROMPT
        if not chat_history or chat_history[0].get("role") != "system":
            chat_history.insert(0, {"role": "system", "content": base_prompt})
        else:
            chat_history[0]["content"] = base_prompt

        # Handle Internet
        final_prompt = prompt
        if use_internet and needs_internet:
            live_data = search_the_web(question)
            if live_data:
                final_prompt = f"{question}\n\n[SYSTEM]: Use this live info: {live_data}"

        chat_history.append({'role': 'user', 'content': final_prompt})
        
        # Keep history short
        temp_history = [chat_history[0]] + chat_history[-10:] if len(chat_history) > 11 else chat_history

        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=temp_history,
                temperature=0.4,
                stream=True
            )

            full_response = ""
            audio_triggered = False

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Pre-cache first sentence for audio while streaming text
                    if not audio_triggered and len(full_response) > 80 and any(p in full_response for p in ['. ', '! ', '? ', '\n']):
                        audio_triggered = True
                        threading.Thread(target=text_to_audio, args=(full_response, voice)).start()
                    
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Save full assistant response
            chat_history[-1]['content'] = question 
            chat_history.append({'role': 'assistant', 'content': full_response})
            save_memory()

            # Final audio URL
            filename = text_to_audio(full_response, voice)
            yield f"data: {json.dumps({'audio': f'/static/{filename}'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    if not os.path.exists('static'): os.makedirs('static')
    app.run(host="0.0.0.0", port=port, debug=False)
