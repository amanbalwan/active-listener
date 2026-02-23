# 🛠️ DevEx Assistant: AI-Powered Friction Logger

An intelligent internal tool designed to capture and analyze developer friction in real-time. This project uses the **Gemini 1.5 Flash** model with **Function Calling** to transform unstructured chat complaints into structured, actionable engineering tickets stored in **Google Cloud Firestore**.

## 🚀 Live Demo Architecture
The application is built with a serverless architecture for maximum scalability and zero maintenance.

* **Frontend:** Minimalist UI (HTML5/CSS3/JavaScript).
* **Backend:** FastAPI (Python 3.11) hosted on **Google Cloud Run**.
* **Intelligence:** Gemini 2.5 Flash (via Google Generative AI SDK).
* **Database:** Google Cloud Firestore (NoSQL) in Native Mode.
* **CI/CD:** Automated builds via **Google Cloud Build** and **Artifact Registry**.



## ✨ Key Features
* **Natural Language Friction Capture:** Developers can vent about tools (Docker, CI/CD, VPN) in plain English.
* **Automated Ticket Structuring:** AI identifies the tool, the specific issue, and the business impact automatically.
* **Admin Dashboard:** Real-time analytics view (`/admin`) that groups issues by frequency and priority.
* **Persistence:** All tickets are saved permanently in Firestore, surviving server restarts.
* **Proximity-Optimized:** Deployed to `us-west1` (Oregon) to minimize latency for PNW-based developers.

## 🛠️ Installation & Local Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd active-listener
    ```

2.  **Set up Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Environment Variables:**
    Create a `.env` file or export your Gemini API Key:
    ```bash
    export GEMINI_API_KEY="your_key_here"
    ```

4.  **Run Locally:**
    ```bash
    uvicorn main:app --reload
    ```

## ☁️ Deployment
This project is configured for one-command deployment to Google Cloud:

```bash
gcloud run deploy devex-assistant \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="YOUR_API_KEY"
