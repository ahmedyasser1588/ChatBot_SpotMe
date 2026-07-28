# 🏆 SpotMe — AI Sports Scouting Platform

**SpotMe** is an AI-powered scouting API that helps clubs, coaches, and scouts discover and evaluate athletes across multiple sports using data-driven **AI Scores**, structured player profiles, and a conversational AI assistant.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Live Demo & Docs](#-live-demo--docs)
- [API Reference](#-api-reference)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

SpotMe combines a structured player database with an **agentic AI assistant** (powered by Gemini function calling) that can answer natural-language scouting questions in Arabic and English — such as *"من هو أفضل مهاجم بناءً على الـ AI Score؟"* — by querying the underlying player data in real time.

---

## ✨ Features

- 🤖 **Conversational AI Scouting Assistant** — ask questions in natural language and get instant, data-backed answers.
- 🔍 **Advanced Player Search** — filter by sport, position, age, AI score, and more.
- 📊 **AI Score System** — a unified performance metric for comparing athletes across sports.
- 🗂️ **Detailed Player Profiles** — physical attributes, recovery rate, injury history, and team info.
- 📈 **Live Database Overview** — real-time stats on total players, covered sports, and last update time.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Hosting** | Vercel |
| **AI Engine** | Gemini API (Agentic / Function Calling) |
| **API Docs** | Swagger / OpenAPI |
| **Data Format** | JSON over REST |

---

## 🚀 Live Demo & Docs

| Resource | Link |
|---|---|
| **Base URL** | [`chat-bot-spot-me-yztv.vercel.app`](https://chat-bot-spot-me-yztv.vercel.app) |
| **Swagger Docs** | [`/docs`](https://chat-bot-spot-me-yztv.vercel.app/docs) |

---

## 📡 API Reference

Full endpoint specs, request/response payloads, and integration examples for frontend and backend developers are documented in **[`INTEGRATION.md`](./INTEGRATION.md)**.

Quick summary of available endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | AI scouting assistant (conversational) |
| `POST` | `/api/search` | Filter players by custom criteria |
| `GET` | `/api/players/{id_or_name}` | Get a single player's full profile |
| `GET` | `/api/overview` | Database stats & metadata |

👉 See **[INTEGRATION.md](./INTEGRATION.md)** for full request/response examples and error handling.

---

## ⚡ Quick Start

```javascript
async function askAI(userQuery) {
  const response = await fetch("https://chat-bot-spot-me-yztv.vercel.app/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [{ role: "user", content: userQuery }]
    })
  });

  const data = await response.text();
  console.log("AI Response:", data);
}

askAI("من هو أفضل مهاجم في القائمة بناءً على الـ AI Score؟");
```

---

## 📁 Project Structure

```
spotme/
├── api/
│   ├── chat.py          # AI assistant endpoint (Gemini function calling)
│   ├── search.py         # Player search & filtering
│   ├── players.py        # Player detail lookup
│   └── overview.py       # Database metadata
├── data/                 # Player dataset
├── INTEGRATION.md         # Full API integration guide
└── README.md              # This file
```

> ℹ️ Adjust this structure to match your actual repo layout before publishing.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — feel free to use, modify, and distribute with attribution.
