Markdown# ⚽ SpotMe Scouting API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Google%20Gemini-API-8E7CC3?style=for-the-badge&logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

A high-performance standalone backend application built with **FastAPI** and integrated with **Google Gemini API** using **Agentic Function Calling**. The service is designed for sports talent scouts to analyze and query candidate datasets across four sports: **Football, Basketball, Handball, and Volleyball**.

---

## ✨ Features

- 🤖 **Agentic AI Assistant**: Natural language querying powered by Google Gemini API.
- 🛠️ **Function Calling (Tool Use)**: Dynamically triggers custom python backend functions to filter and retrieve structured JSON data accurately.
- ⚡ **Real-Time Streaming Response**: Supports streaming AI chat outputs for instant UI rendering.
- 📊 **Multi-Sport Scouting Logic**: Multi-criteria query engine supporting age, height, AI score, injury history, recovery rate, and performance metrics.
- 🏗️ **Clean Architecture**: Standard separation of concerns (Routes, Services, Models, Utilities) adhering to SOLID principles.

---

## 🏗️ Project Architecture

```text
backend/
│
├── app.py                     # FastAPI Application Entrypoint
├── config.py                  # Global Configuration & Environment Variables
├── requirements.txt           # Project Dependencies
├── .env                       # API Credentials & Environment Variables
│
├── api/
│   └── routes.py              # REST API Endpoints Handler
│
├── services/
│   ├── gemini_service.py      # Gemini API Integration & Agent Prompt Engineering
│   └── player_service.py      # Core Scouting & Data Processing Engine
│
├── models/
│   └── schemas.py             # Pydantic Input/Output Validation Schemas
│
├── data/
│   └── players.json           # Structured Multi-sport Player Dataset
│
└── prompts/
    └── system_prompt.txt      # System Instructions & Agent Guardrails
🚀 Getting StartedPrerequisitesPython 3.10+Google Gemini API Key (Obtain from Google AI Studio)Installation & SetupClone the repository:Bashgit clone [https://github.com/YOUR_USERNAME/spotme-backend.git](https://github.com/YOUR_USERNAME/spotme-backend.git)
cd spotme-backend
Create and activate a virtual environment:Windows:Bashpython -m venv venv
venv\Scripts\activate
Linux / macOS:Bashpython3 -m venv venv
source venv/bin/activate
Install dependencies:Bashpip install -r requirements.txt
Environment Configuration:Create a .env file in the root directory:مقتطف الرمزGEMINI_API_KEY=your_actual_gemini_api_key
DATA_PATH=data/players.json
SYSTEM_PROMPT_PATH=prompts/system_prompt.txt
Run the server:Bashpython app.py
The server will start on http://localhost:8000📡 API Endpoints SummaryMethodEndpointDescriptionPOST/api/chatAI Chat completion with Gemini + Function Calling (Supports Stream)POST/api/searchSearch & filter player datasets based on custom criteriaGET/api/players/{id_or_name}Retrieve individual player profile detailsGET/api/overviewSummarized database metadata across all sportsPOST/api/statsAggregated statistical metrics for specific performance attributes💡 Interactive Swagger documentation is accessible directly at http://localhost:8000/docs when the app is running.💻 Sample API UsageChat Endpoint (POST /api/chat)Request Payload:JSON{
  "messages": [
    {
      "role": "user",
      "content": "Who is the top football striker with an AI score higher than 80?"
    }
  ]
}
🛡️ LicenseDistributed under the MIT License. See LICENSE for more information.
