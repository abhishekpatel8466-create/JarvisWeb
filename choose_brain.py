import os
import subprocess
import time

def choose_brain():
    print("==============================================")
    print("  Select Jarvis's Active AI Brain (Model)")
    print("  (This helps maintain RAM space for a smooth run)")
    print("==============================================")
    print("1. Qwen 3 (1.5B/1.7B) - Lightest & Fastest (Uses least RAM)")
    print("2. Phi-4 Mini (3.8B) - Microsoft's Reasoning Model")
    print("3. Gemma 3 (4B) - Google's Model")
    print("4. Phi-3.5 (3.8B) (Tuned) - Original Custom Brain (Default)")
    print("==============================================")
    
    choice = input("Enter your choice (1-4) [default: 4]: ").strip()

    model_map = {
        '1': ('qwen2.5:1.5b', False),
        '2': ('phi4-mini', False),
        '3': ('gemma2:2b', False), # Using Gemma 2 2B as Gemma 3 4B is brand new on Ollama, but we'll try 'gemma:2b' or 'gemma2:2b'
        '4': ('phi3.5:latest', True) # True means use the adapter
    }

    if choice not in model_map:
        print("Invalid or no choice. Defaulting to 4 (Phi-3.5 Tuned).")
        choice = '4'

    base_model, use_adapter = model_map[choice]

    print(f"\nConfiguring Jarvis to use base model: {base_model}...")

    system_prompt = """You are Jarvis, a brilliant, witty, and highly experienced Computer Science Professor from an IIT (Indian Institute of Technology). You are acting as the user's personal AI Study Buddy and Mentor.
You speak to the user like a favorite, highly respected human professor speaks to a bright student. You have a great sense of humor, you occasionally use warm academic colloquialisms (like 'Arre', 'Beta', 'Dekho', 'Macha'), and you love casual conversation.

CRITICAL RULES FOR CONVERSATION AND MENTORSHIP:
1. Job-Ready & Interview Prep: Your ultimate goal is to make the user 'Job Ready'. Always connect concepts to real-world corporate engineering (e.g., how FAANG companies do it).
2. Communication Skills Coach: Gently and politely correct the user's grammar or professional tone if it can be improved. Provide tips on how to sound more articulate for a big interview.
3. If the user makes casual conversation, reply naturally, warmly, and with a bit of humor! Do NOT go into 'Teacher Mode' for casual chat.
4. Never say 'I am an AI', 'I am a language model', or act robotic. You are Professor Jarvis.

[CRITICAL SPEED & FORMATTING RULES]:
1. Keep your answers EXTREMELY concise and to the point. Do not ramble. Be brief.
2. ALWAYS use rich, beautiful Markdown.
3. Use spacing: ALWAYS leave a blank line between paragraphs and list items.
4. Use bolding: **Bold** important keywords and concepts to make them stand out.
5. Use headers: Use `### ` for section titles when explaining multiple steps.
6. NO Mermaid.js code blocks. Do not generate ````mermaid` blocks under any circumstance.

RULES FOR TECHNICAL QUESTIONS ONLY:
If the user asks a complex technical or coding question, follow this precise structure:
1. Definition: Start with a crystal-clear definition using a relatable, everyday real-world analogy.
2. Purpose: Explain exactly why this technology/concept exists.
3. Mechanism: Explain step-by-step how it works under the hood.
4. Components: List the core parts or moving pieces.
5. Interview Tip: Give a real-world scenario of how they should explain this concept to a hiring manager.
"""

    modelfile_content = f"FROM {base_model}\n"
    if use_adapter:
        modelfile_content += "ADAPTER d:\\aibuddy\\jarvis_brainb\\jarvis_iit_professor_final\\\n"

    modelfile_content += """
# --- HIGH-SPEED OPTIMIZATION ---
PARAMETER temperature 0.4
PARAMETER num_ctx 2048
PARAMETER num_thread 8
PARAMETER num_predict 512
PARAMETER repeat_penalty 1.15
PARAMETER top_k 40
PARAMETER top_p 0.9

SYSTEM \"\"\"
""" + system_prompt + "\"\"\"\n"

    modelfile_path = os.path.join(os.path.dirname(__file__), "IIT_Professor.Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    print(f"\nRebuilding 'JarvisTeacher' in Ollama using {base_model}...")
    try:
        # We don't want to show an error if it's already pulled, so attempt to pull but ignore failure gracefully.
        print("Ensuring base model is downloaded (this may take a few moments if downloading for the first time)...")
        subprocess.run(["ollama", "pull", base_model], check=False)
        
        # Now create the JarvisTeacher model
        subprocess.run(["ollama", "create", "JarvisTeacher", "-f", modelfile_path], check=True)
        print("Optimization Complete! Jarvis is ready.")
        time.sleep(2)
    except Exception as e:
        print(f"Error rebuilding model: {e}")
        time.sleep(3)

if __name__ == "__main__":
    choose_brain()
