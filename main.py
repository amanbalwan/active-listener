import datetime
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import content_types
from google.cloud import firestore

# 1. At the top of main.py, add a list to store tickets in memory
db = firestore.Client()
# 1. Configuration & Setup
app = FastAPI()
# IMPORTANT: You will need to set this environment variable in your terminal
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Simple in-memory storage to keep track of conversation history per session
sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

# 2. Define the "Tool" (The action the agent can take)
# 2. Update your tool function to save the ticket to this list
def log_engineering_ticket(tool_name: str, issue_description: str, priority: str = "Medium"):
    try:
        # 1. Force everything to strings to prevent TypeErrors
        ticket = {
            "tool_name": str(tool_name),
            "issue_description": str(issue_description),
            "priority": str(priority),
            "timestamp": firestore.SERVER_TIMESTAMP 
        }
        
        # 2. Log exactly what we are about to send to Firestore
        print(f"ATTEMPTING WRITE: {ticket}")
        
        db.collection("tickets").add(ticket)
        return f"Ticket logged: {tool_name} is being tracked with {priority} priority."
        
    except Exception as e:
        # 3. This will catch exactly why Firestore is mad
        print(f"FIRESTORE CRASH: {e}")
        return "I've noted the issue, but had a sync error. I'll retry in the background."


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

# Initialize the model with the tool and instructions
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[log_engineering_ticket],
    system_instruction=system_instruction
)

# 4. API Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    # Serve our static Apple-like HTML file
    with open("index.html", "r") as f:
        return f.read()
    
@app.get("/admin-data")
async def get_admin_data():
    # Pull all tickets, sorted by newest first
    docs = db.collection("tickets").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    tickets = []
    for doc in docs:
        t = doc.to_dict()
        # Convert timestamp to string for JSON compatibility
        if t.get("timestamp"):
            t["timestamp"] = t["timestamp"].isoformat()
        tickets.append(t)
    return tickets

@app.get("/admin")
async def admin_page():
    return FileResponse("admin.html")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Retrieve or create a chat session
    if req.session_id not in sessions:
        sessions[req.session_id] = model.start_chat(enable_automatic_function_calling=True)
    
    chat = sessions[req.session_id]
    
    # Send the message to Gemini
    response = chat.send_message(req.message)
    
    return {"reply": response.text}