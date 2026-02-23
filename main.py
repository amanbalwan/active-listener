import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
from google.cloud import firestore

# 1. Configuration & Setup
app = FastAPI()
db = firestore.Client()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

# 2. Define the Tool (Simplified for Efficiency)
def log_engineering_ticket(tool_name: str, issue_description: str, priority: str = "Medium"):
    """Logs a developer friction ticket to the database."""
    try:
        ticket = {
            "tool_name": str(tool_name),
            "issue_description": str(issue_description),
            "priority": str(priority),
            "timestamp": firestore.SERVER_TIMESTAMP 
        }
        db.collection("tickets").add(ticket)
        return f"SUCCESS: Logged {priority} ticket for {tool_name}."
    except Exception as e:
        print(f"Error saving ticket: {e}")
        return "I encountered a technical issue while saving the ticket. Please try again later."

# 3. Configure the Agent
system_instruction = """
You are an Employee Experience Agent for the Engineering team.
Your goal is to gather specific feedback about Developer Tooling and Process Friction.

To log a valid ticket, you MUST know these 3 things:
1. The specific tool (e.g., GitHub, Docker, CI/CD pipeline, local compiler).
2. The specific issue (e.g., timing out, throwing a memory error).
3. The business impact (e.g., can't merge PRs, wasting 2 hours a day).

If the user complains but you are missing any of these 3 things, ask a brief, polite clarifying question.
Once you have all 3 pieces of information, immediately call the 'log_engineering_ticket' tool. Do not ask for permission to log it.
Keep your conversational responses short and empathetic.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[log_engineering_ticket],
    system_instruction=system_instruction
)

# 4. API Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("index.html", "r") as f:
        return f.read()
    
@app.get("/admin-data")
async def get_admin_data():
    docs = db.collection("tickets").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    tickets = []
    for doc in docs:
        t = doc.to_dict()
        if t.get("timestamp"):
            t["timestamp"] = t["timestamp"].isoformat()
        tickets.append(t)
    return tickets

@app.get("/admin")
async def admin_page():
    return FileResponse("admin.html")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. CHECK BEFORE TALKING TO GEMINI
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent_tickets = db.collection("tickets").where("timestamp", ">=", cutoff).stream()
    
    if len(list(recent_tickets)) >= 3:
        return {"reply": "I'm sorry, our system has reached its daily limit of 3 tickets. Please come back tomorrow!"}

    # 2. PROCEED TO GEMINI
    if req.session_id not in sessions:
        sessions[req.session_id] = model.start_chat(enable_automatic_function_calling=True)
    
    chat = sessions[req.session_id]
    response = chat.send_message(req.message)
    return {"reply": response.text}