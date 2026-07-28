# 🔗 SpotMe API Integration Guide

This guide provides the technical specifications, endpoints, and request/response payloads required to integrate with the **SpotMe Scouting API**.

---

## 📋 Table of Contents

- [Base URL & Documentation](#-base-url--documentation)
- [Authentication](#-authentication)
- [API Endpoints](#-api-endpoints-specification)
  - [1. AI Chat Assistant](#1️⃣-ai-chat-assistant-agentic-gemini-api--function-calling)
  - [2. Direct Player Search & Filtering](#2️⃣-direct-player-search--filtering)
  - [3. Get Player Details by ID or Name](#3️⃣-get-player-details-by-id-or-name)
  - [4. Database Overview & Metadata](#4️⃣-database-overview--metadata)
- [Error Handling](#-error-handling)
- [Quick Start Example](#️-quick-javascript--fetch-example)
- [Support](#-support)

---

## 🌐 Base URL & Documentation

| Resource | URL |
|---|---|
| **Base URL** | `https://chat-bot-spot-me-yztv.vercel.app` |
| **Interactive Swagger Docs** | `https://chat-bot-spot-me-yztv.vercel.app/docs` |

> 💡 Use the Swagger docs for live request testing directly in the browser.

---

## 🔐 Authentication

All endpoints are currently open (no auth token required). If an API key or auth header is introduced later, it will be documented here — check back before going to production.

---

## 📡 API Endpoints Specification

### 1️⃣ AI Chat Assistant (Agentic Gemini API + Function Calling)

Interacts with the AI scouting agent. The agent autonomously queries structured player data using internal function calling when needed.

| | |
|---|---|
| **Endpoint** | `POST /api/chat` |
| **Full URL** | `https://chat-bot-spot-me-yztv.vercel.app/api/chat` |
| **Headers** | `Content-Type: application/json` |

**Request Payload Example:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "من هو أفضل مهاجم في القائمة بناءً على الـ AI Score؟"
    }
  ]
}
```

**Response:**
Returns a direct plain text / markdown response (or a streamed response) representing the AI agent's answer.

---

### 2️⃣ Direct Player Search & Filtering

Filters and retrieves specific player records based on custom criteria (sport, position, score limits, etc.).

| | |
|---|---|
| **Endpoint** | `POST /api/search` |
| **Full URL** | `https://chat-bot-spot-me-yztv.vercel.app/api/search` |
| **Headers** | `Content-Type: application/json` |

**Request Payload Example:**
```json
{
  "sport": "football",
  "position": "ST",
  "min_ai_score": 80,
  "limit": 5
}
```

**Response Example:**
```json
[
  {
    "id": "P0003",
    "name": "Ahmed Ali",
    "sport": "football",
    "position": "ST",
    "age": 21,
    "ai_score": 88.5,
    "team": "Zamalek"
  }
]
```

---

### 3️⃣ Get Player Details by ID or Name

Retrieves the complete profile of a single player using their ID or name.

| | |
|---|---|
| **Endpoint** | `GET /api/players/{id_or_name}` |
| **Full URL** | `https://chat-bot-spot-me-yztv.vercel.app/api/players/P0003` |

**Response Example:**
```json
{
  "id": "P0003",
  "name": "Ahmed Ali",
  "sport": "football",
  "position": "ST",
  "age": 21,
  "height_cm": 185,
  "weight_kg": 78,
  "ai_score": 88.5,
  "recovery_rate": 92.0,
  "injury_history": "None"
}
```

---

### 4️⃣ Database Overview & Metadata

Returns statistical summaries and metadata regarding total players, sports covered, and available categories.

| | |
|---|---|
| **Endpoint** | `GET /api/overview` |
| **Full URL** | `https://chat-bot-spot-me-yztv.vercel.app/api/overview` |

**Response Example:**
```json
{
  "total_players": 150,
  "sports": ["football", "basketball", "handball", "volleyball"],
  "last_updated": "2026-07-28"
}
```

---

## ⚠️ Error Handling

All endpoints return standard HTTP status codes. Handle these on the client side:

| Status Code | Meaning |
|---|---|
| `200 OK` | Request succeeded |
| `400 Bad Request` | Invalid or missing parameters in the payload |
| `404 Not Found` | Player ID/name not found |
| `500 Internal Server Error` | Unexpected server-side error |

---

## 🛠️ Quick JavaScript / Fetch Example

```javascript
async function askAI(userQuery) {
  const response = await fetch("https://chat-bot-spot-me-yztv.vercel.app/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      messages: [
        { role: "user", content: userQuery }
      ]
    })
  });

  const data = await response.text();
  console.log("AI Response:", data);
}
```

---

## 🧩 Support

For questions, bugs, or integration issues, please open an issue in this repository or reach out to the backend team directly.
