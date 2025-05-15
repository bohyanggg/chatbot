import os
import json
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

# Request schema
class ChatRequest(BaseModel):
    session_id: str
    message: str

# Helper functions
def find_faq_answer(msg: str) -> str | None:
    for item in faqs:
        if msg.lower() == item["question"].lower():
            return item["answer"]
    return None

def find_myth_bust(msg: str) -> str | None:
    for item in myths:
        if msg.lower() == item["myth"].lower():
            return item["bust"]
    return None

# Chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest):
    session = sessions.setdefault(req.session_id, {})
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
                    {"role": "system", "content": "You are a helpful assistant specialized in contact lens guidance."},
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