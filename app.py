from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import ollama
import edge_tts
import asyncio
import uuid
import json
import requests
import re
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

if not os.path.exists("static"):
    os.makedirs("static")

MEMORY_FILE = "Jarvis_Memory.json"
chat_history = []

# ==========================================
# 1. Load the Long-Term Diary (Memory)
# ==========================================
def load_memory():
    global chat_history
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                saved_memory = json.load(f)
                # Ensure the history doesn't grow to 10,000 lines and crash the computer
                # Keep the last 15 interactions
                chat_history = saved_memory[-15:]
                print(f"Jarvis: Woke up and successfully remembered {len(chat_history)} past interactions!")
        except Exception as e:
            chat_history = []
            print("Jarvis: Creating a fresh new Diary.")
    else:
        chat_history = []

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(chat_history, f)

load_memory()

# ==========================================
# 2. Textbooks
# ==========================================
textbook_context = ""
if os.path.exists("textbooks"):
    for file in os.listdir("textbooks"):
        if file.endswith(".txt"):
            with open(os.path.join("textbooks", file), "r", encoding="utf-8") as f:
                textbook_context += f.read() + "\n\n"

# REMOVE OLD SYSTEM PROMPT overriding the custom Modelfile 'JarvisTeacher'
# We purge any old 'system' entries from the memory so the Modelfile is the single source of truth
chat_history = [msg for msg in chat_history if msg.get("role") != "system"]


# ==========================================
# 3. Web Search Function (SearXNG -> DDG -> Wiki -> Scrape)
# ==========================================
def search_the_web(query):
    print(f"Jarvis: Initiating 4-Tier Search for: {query}")
    import urllib.parse
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    web_context = "I found this LIVE info:\n\n"
    found_data = False

    try:
        # Tier 1: SearXNG (Free public instances)
        searx_url = f"https://searx.be/search?q={urllib.parse.quote(query)}&format=json"
        resp = requests.get(searx_url, headers=headers, timeout=5).json()
        if 'results' in resp and len(resp['results']) > 0:
            for r in resp['results'][:2]:
                web_context += f"- [SearXNG]: {r.get('content', '')}\n"
            found_data = True
    except:
        pass

    if not found_data:
        try:
            # Tier 2: DuckDuckGo Lite HTML Scrape
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            soup = BeautifulSoup(requests.get(ddg_url, headers=headers, timeout=5).text, 'html.parser')
            results = soup.find_all('a', {'class': 'result__snippet'})
            if results:
                for r in results[:2]:
                    web_context += f"- [DuckDuckGo]: {r.text}\n"
                found_data = True
        except:
            pass

    if not found_data:
        try:
            # Tier 3: Wikipedia
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exsentences=3&titles={urllib.parse.quote(query)}&explaintext=1&formatversion=2&format=json"
            resp = requests.get(wiki_url, timeout=5).json()
            if 'query' in resp and 'pages' in resp['query']:
                page = resp['query']['pages'][0]
                if 'extract' in page:
                    web_context += f"- [Wikipedia]: {page['extract']}\n"
                    found_data = True
        except:
            pass

    return web_context if found_data else None

def clean_text_for_speech(text):
    """Strips Markdown symbols so the Voice Engine doesn't speak weird punctuation."""
    # 0. Completely remove the <PLAYGROUND> tags and everything inside them from the spoken audio!
    text = re.sub(r'<PLAYGROUND>.*?</PLAYGROUND>', ' (I have generated a diagram in the Playground on your right) ', text, flags=re.DOTALL)
    
    # 1. Replace multi-line code blocks with a friendly voice phrase
    text = re.sub(r'```.*?```', ' (I have written the code block for you on the screen) ', text, flags=re.DOTALL)
    # 2. Remove inline code backticks
    text = re.sub(r'`(.*?)`', r'\1', text)
    # 3. Remove bold/italics asterisks
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # 4. Remove URL links but keep the title
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 5. Remove bullet points and hashtags
    text = text.replace('#', '')
    text = text.replace('-', ' ')
    text = text.replace('_', ' ')
    
    return text.strip()

async def generate_speech(text, voice, file_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(file_path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history
    
    # Check if running in a Replit environment and forward headers
    if 'REPL_ID' in os.environ:
        # Replit uses X-Forwarded-For for client IP
        # And X-Forwarded-Proto for scheme (http/https)
        if 'X-Forwarded-For' in request.headers:
            request.remote_addr = request.headers['X-Forwarded-For'].split(',')[0].strip()
        if 'X-Forwarded-Proto' in request.headers:
            request.url_root = request.headers['X-Forwarded-Proto'] + '://' + request.host + '/'

    data = request.json
    question = data.get('question', '')
    voice = data.get('voice', 'en-IN-PrabhatNeural')
    mode = data.get('mode', 'mentor')
    use_internet = data.get('useInternet', True)
    history_mode = data.get('historyMode', 'keep')
    
    # If the user selected "Start Fresh", wipe the memory before processing the question
    if history_mode == "clear":
        chat_history.clear()
        save_memory()
    
    # Check if they randomly ask for weather/news/current events
    needs_internet = any(word in question.lower() for word in ['today', 'current', 'news', 'weather', 'latest', 'price of', 'who won', 'search'])
    
    prompt = question
    
    # Mode Handling (Dynamically changes Jarvis's personality for this specific question)
    mode_instructions = {
        "mentor": "",
        "standup": "[SYSTEM INSTRUCTION]: We are doing an Agile Daily Standup simulation. Ask the user for their updates. Act like a supportive Engineering Manager. Critically evaluate how concise and professional their update sounds.",
        "client": "[SYSTEM INSTRUCTION]: You are a non-technical Business Executive. The user is explaining a technical concept to you. If they use confusing IT jargon without explaining it, stop them and ask them to explain it more simply.",
        "pr": "[SYSTEM INSTRUCTION]: We are doing a Pull Request Code Review simulation. Act as a Senior Teammate. Ask probing questions about their logic, readability, and how well they communicate their thought process.",
        "star": "[SYSTEM INSTRUCTION]: We are practicing HR Behavioral Interviews. Ask the user a behavioral question. Critically evaluate their answer based on the STAR method (Situation, Task, Action, Result) and give them feedback on their communication skills."
    }
    
    if mode != "mentor":
        prompt = f"{mode_instructions.get(mode, '')}\n\nUser Question: {prompt}"
    
    # 3. If they asked something related to today/news AND internet is allowed
    if use_internet and needs_internet:
        live_data = search_the_web(question)
        if live_data:
            # We secretly feed the live data into the prompt, without the user seeing it
            prompt = f"{question}\n\n[SECRET SYSTEM INSTRUCTION]: Do not say you searched the internet. Just answer the user's question naturally using this live information you just downloaded: \n{live_data}"

    # Add user's new question to memory
    chat_history.append({'role': 'user', 'content': prompt})
    
    # Keep history from getting too long (keep last 15 messages + system prompt)
    if len(chat_history) > 16:
        chat_history = [chat_history[0]] + chat_history[-15:]

    try:
        # Ask Jarvis
        response = ollama.chat(model='JarvisTeacher', messages=chat_history)
        answer = response['message']['content']
        
        # Save Jarvis's answer to memory so it remembers what it just said!
        # Save the *real* user question without the secret system prompt attached to history
        chat_history[-1]['content'] = question 
        chat_history.append({'role': 'assistant', 'content': answer})
        
        # Save the diary to the computer hard drive!
        save_memory()
        
    except Exception as e:
        answer = "I'm sorry, my core logic engine went offline."
        print(e)

    # Generate Voice (Skip if the user wants the instant Native Browser Voice)
    audio_url = ""
    if voice != 'native':
        filename = f"audio_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join("static", filename)
        
        # Strip markdown symbols so it doesn't mispronounce "asterisk asterisk" or weird numbers
        cleaned_speech = clean_text_for_speech(answer)
        
        try:
            asyncio.run(generate_speech(cleaned_speech, voice, file_path))
            audio_url = f"/static/{filename}"
        except Exception as e:
            audio_url = ""

    return jsonify({"answer": answer, "audio": audio_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Jarvis (LIVE INTERNET EDITION) starting on http://0.0.0.0:{port}/")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
