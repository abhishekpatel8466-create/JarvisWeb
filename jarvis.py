import os
import ollama
import pyttsx3

# Setup the Native Windows Voice Engine
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('rate', 160)
except Exception as e:
    print(f"Jarvis: Voice engine failed to start. {e}")
    engine = None

def speak(text):
    if engine:
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"\nJarvisTeacher Text: {text}\n")

import choose_brain

def start_jarvis():
    choose_brain.choose_brain()
    print("Jarvis: Speed-scanning your textbooks...")
    
    # 2. Read textbooks
    context = ""
    if os.path.exists("textbooks"):
        for file in os.listdir("textbooks"):
            if file.endswith(".txt"):
                with open(os.path.join("textbooks", file), "r", encoding="utf-8") as f:
                    context += f.read() + "\n\n"
                    
    print("\n==================================")
    print(" Jarvis Teacher is Online!")
    print(" (Type 'quit' to exit)")
    print("==================================\n")
    
    speak("Hello! I am your IIT Professor. I am ready to teach you.")
    
    while True:
        try:
            print("\n-------------------------")
            question = input("Student: ")
            
            if question.lower() == 'quit':
                speak("Goodbye Student. Keep learning!")
                break
                
            # 3. Add textbook knowledge
            prompt = question
            if context:
                prompt = f"Using this exact textbook information:\n\n{context}\n\nAnswer the student's question clearly and simply using real world analogies: {question}"
                
            print("\nJarvisTeacher is thinking...\n")
            
            response = ollama.chat(model='JarvisTeacher', messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            answer = response['message']['content']
            
            print(f"JarvisTeacher: {answer}")
            speak(answer)
            
        except (KeyboardInterrupt, EOFError):
            speak("Goodbye!")
            break

if __name__ == "__main__":
    start_jarvis()
