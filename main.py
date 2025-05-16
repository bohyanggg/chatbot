import os
import json
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI


from fastapi.staticfiles import StaticFiles


# Load environment variables
print("OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))

# Initialize FastAPI
app = FastAPI()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# In-memory session store
sessions: dict[str, dict] = {}

# Load data files
with open("faqs.json") as f:
    faqs = json.load(f)
with open("myths.json") as f:
    myths = json.load(f)

# Initialize OpenAI client and cache embeddings
client = OpenAI()
faq_vectors = []
myth_vectors = []

def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return np.array(response.data[0].embedding)

for item in faqs:
    item['embedding'] = get_embedding(item['question'])
    faq_vectors.append(item)

for item in myths:
    item['embedding'] = get_embedding(item['myth'])
    myth_vectors.append(item)

# Request schema
class ChatRequest(BaseModel):
    session_id: str
    message: str

# Helper functions
def find_faq_answer(msg: str) -> str | None:
    msg_vector = get_embedding(msg)
    best_match = None
    best_score = 0.0
    for item in faq_vectors:
        score = np.dot(msg_vector, item['embedding']) / (np.linalg.norm(msg_vector) * np.linalg.norm(item['embedding']))
        if score > best_score:
            best_score = score
            best_match = item
    if best_score > 0.9:
        return best_match["answer"]
    return None

def find_myth_bust(msg: str) -> str | None:
    msg_vector = get_embedding(msg)
    best_match = None
    best_score = 0.0
    for item in myth_vectors:
        score = np.dot(msg_vector, item['embedding']) / (np.linalg.norm(msg_vector) * np.linalg.norm(item['embedding']))
        if score > best_score:
            best_score = score
            best_match = item
    if best_score > 0.9:
        return best_match["bust"]
    return None

# Chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest):
    session = {}
    sessions[req.session_id] = session
    msg = req.message.strip()

    if not msg and "history" not in session:
        session["history"] = []
        session["greeted"] = True
        return {"response": "Hi, I'm your Lens4U assistant. Do you have any questions or need help choosing a contact lens?"}

    if "history" not in session:
        session["history"] = []
        session["greeted"] = True

    # 1) FAQ exact match
    faq = find_faq_answer(msg)
    if faq:
        return {"response": faq}

    # 2) Myth busting
    myth = find_myth_bust(msg)
    if myth:
        return {"response": myth}



    history = session.get('history', [])
    history.append({"role": "user", "content": msg})
    context = history[-10:]  # last 10 turns
    answer = None

    for attempt in range(2):
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are the Lens4U assistant, a helpful assistant specialized in contact lens guidance."},
                    *context
                ],
                max_tokens=150,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            history.append({"role": "assistant", "content": answer})
            session["history"] = history
            break
        except Exception as e:
            print("OpenAI error:", e)
            if attempt == 1:
                answer = "Sorry, I'm experiencing an issue. Please try again."
    return {"response": answer}