import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import content_types

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
def log_engineering_ticket(tool_name: str, specific_issue: str, business_impact: str) -> str:
    """
    Logs a structured ticket for the Platform Engineering team.
    Only call this when you clearly know the tool, the issue, and the impact.
    """
    # In a real system design, you would push this payload to Apache Kafka here
    ticket_payload = {
        "status": "LOGGED",
        "route_to": "Platform_Engineering",
        "data": {
            "tool": tool_name,
            "issue": specific_issue,
            "impact": business_impact
        }
    }
    
    # Print to console so we can see it working during the demo
    print("\n" + "="*40)
    print("🎫 NEW TICKET LOGGED VIA AGENT:")
    print(json.dumps(ticket_payload, indent=2))
    print("="*40 + "\n")
    
    return "Ticket successfully logged. The platform team has been notified."

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

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Retrieve or create a chat session
    if req.session_id not in sessions:
        sessions[req.session_id] = model.start_chat(enable_automatic_function_calling=True)
    
    chat = sessions[req.session_id]
    
    # Send the message to Gemini
    response = chat.send_message(req.message)
    
    return {"reply": response.text}