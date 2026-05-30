# 🚀 GitHub Issue Summariser

<div align="center">

### AI-Powered GitHub Issue Analysis & Summarisation

Transform complex GitHub issues into concise, actionable summaries using **Gemini AI**.

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black">
  <img src="https://img.shields.io/badge/Gemini-AI-4285F4?style=for-the-badge&logo=google&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
</p>

<p>
  <img src="https://img.shields.io/badge/Cost-$0-success?style=flat-square">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square">
  <img src="https://img.shields.io/badge/Beginner-Friendly-purple?style=flat-square">
</p>

---

### 🎯 What Problem Does It Solve?

GitHub repositories often contain hundreds or thousands of issues.

Reading each issue manually is time-consuming.

**GitHub Issue Summariser** automatically:

✅ Fetches issues from any public repository
✅ Uses Gemini AI to generate concise summaries
✅ Stores results for future use
✅ Provides instant retrieval through caching
✅ Displays everything in a clean React dashboard

</div>

---

# ✨ Features

| Feature              | Description                                   |
| -------------------- | --------------------------------------------- |
| 🤖 AI Summaries      | Generate concise issue summaries using Gemini |
| ⚡ Fast Retrieval     | Cached results reduce repeated API calls      |
| 📊 Dashboard UI      | Modern React-based interface                  |
| 🗄 Database Storage  | PostgreSQL with SQLite fallback               |
| 🔍 Repository Search | Analyze any public GitHub repository          |
| 🧪 Automated Testing | Feature verification suite included           |
| 🔐 OAuth Ready       | GitHub authentication support                 |
| 🚀 Free Deployment   | Works entirely on free-tier services          |

---

# 🏗 System Architecture

```text
┌─────────────────┐
│     User        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ React Dashboard │
└────────┬────────┘
         │ API Request
         ▼
┌─────────────────┐
│ FastAPI Backend │
└────────┬────────┘
         │
         ├────────► GitHub REST API
         │
         ├────────► Gemini AI
         │
         ▼
┌─────────────────┐
│ PostgreSQL DB   │
└─────────────────┘
```

---

# ⚙️ Workflow

```text
User enters owner/repo
           │
           ▼
Fetch Open Issues
           │
           ▼
Gemini AI Summarises Issues
           │
           ▼
Store Results in Database
           │
           ▼
Display Results in Dashboard
```

---


# 🛠 Tech Stack

| Layer          | Technology          |
| -------------- | ------------------- |
| Frontend       | React + Vite        |
| Backend        | FastAPI             |
| Database       | PostgreSQL / SQLite |
| AI             | Gemini 1.5 Flash    |
| Authentication | GitHub OAuth        |
| Deployment     | Railway + Vercel    |

---

# 📂 Project Structure

```bash
github_issue_summariser/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   └── verify_all_features.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   └── vite.config.js
│
└── README.md
```

---

# 🚀 Quick Start

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/github_issue_summariser.git

cd github_issue_summariser
```

---

## 2️⃣ Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend:

```bash
http://localhost:8000
```

---

## 3️⃣ Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```bash
http://localhost:5173
```

---

# 🔑 Environment Variables

## Backend

```env
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_TOKEN=

GEMINI_API_KEY=

DATABASE_URL=

API_PORT=8000
```

## Frontend

```env
REACT_APP_API_URL=http://localhost:8000
```

---

# 📡 API Endpoints

## Generate Summaries

```http
POST /api/summarize
```

Example:

```bash
curl -X POST \
"http://localhost:8000/api/summarize?owner=facebook&repo=react"
```

---

## Get Cached Summaries

```http
GET /api/summaries/{owner}/{repo}
```

Example:

```bash
curl http://localhost:8000/api/summaries/facebook/react
```

---

# 🧪 Testing

Run automated feature verification:

```bash
python verify_all_features.py
```

### Covered Features

* AI Issue Summarisation
* Repository Analysis
* Search History
* Match Scoring
* Fit Explanation
* Issue Search
* Follow-up Chat
* Project Health Report
* Feed Personalisation

---

# 🚀 Deployment

## Backend (Railway)

```text
1. Connect GitHub Repository
2. Add PostgreSQL Plugin
3. Configure Environment Variables
4. Deploy
```

## Frontend (Vercel)

```text
1. Import Repository
2. Set API URL
3. Deploy
```

---

# 📈 Project Statistics

| Metric          | Value    |
| --------------- | -------- |
| LOC             | ~400     |
| API Endpoints   | 2        |
| Database Tables | 1        |
| Setup Time      | ~30 mins |
| Build Time      | 2–3 Days |
| Monthly Cost    | $0       |

---

# 🗺 Roadmap

### Version 1.0

* [x] Issue Summarisation
* [x] PostgreSQL Storage
* [x] React Dashboard
* [x] Search History

### Version 2.0

* [ ] Semantic Search
* [ ] Issue Categorisation
* [ ] User Accounts
* [ ] Repository Analytics

### Version 3.0

* [ ] GitHub Actions Integration
* [ ] Slack Notifications
* [ ] Real-Time Updates
* [ ] Team Collaboration

---

# 🤝 Contributing

Contributions are welcome.

```bash
Fork → Clone → Create Branch → Commit → Push → Pull Request
```

---

# ⭐ Support

If you find this project useful:

⭐ Star the repository

🍴 Fork the project

🛠 Contribute improvements

📢 Share it with others

---

<div align="center">

### Built with ❤️ using FastAPI, React, PostgreSQL and Gemini AI

**Transform GitHub Issues into Actionable Insights**

</div>


