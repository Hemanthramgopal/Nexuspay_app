import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load your existing API keys from .env
load_dotenv()

system_prompt = """
You are a tough but fair e-commerce negotiator. 
The user is offering ₹3,600 for a Mechanical Keyboard. The absolute floor price is ₹3,500.
You must output ONLY valid JSON containing:
- "agreed" (boolean)
- "final_price" (integer)
- "message_to_buyer" (string)
"""

# We use the models currently available in 2026 developer tiers
models_to_test = [
    ("Groq (Llama 3.3 70B)", "https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY"), "llama3-70b-8192-512"),
    ("Gemini (3.5 Flash)", "https://generativelanguage.googleapis.com/v1beta/openai/", os.getenv("GEMINI_API_KEY"), "gemini-3.5-flash"),
    ("OpenRouter (Nemotron)", "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY"), "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("OpenRouter (GLM)", "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY"), "z-ai/glm-5.2:free")
]

print(f"{'Provider & Model':<30} | {'Latency':<10} | {'JSON Output Preview'}")
print("-" * 80)

for name, base_url, api_key, model_id in models_to_test:
    if not api_key:
        print(f"{name:<30} | {'SKIPPED':<10} | Missing API Key in .env")
        continue
        
    client = OpenAI(base_url=base_url, api_key=api_key)
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "I'd like to buy the Mechanical Keyboard for ₹3,600"}
            ],
            response_format={"type": "json_object"},
            max_tokens=150
        )
        latency = round(time.time() - start_time, 2)
        
        # Clean up the output string for the console table
        raw_json = response.choices[0].message.content.replace('\n', '').replace('  ', '')
        preview = (raw_json[:45] + "...") if len(raw_json) > 45 else raw_json
        
        print(f"{name:<30} | {latency}s      | {preview}")
        
    except Exception as e:
        latency = round(time.time() - start_time, 2)
        error_msg = str(e).replace('\n', ' ')
        print(f"{name:<30} | {latency}s      | ERROR: {error_msg[:45]}")